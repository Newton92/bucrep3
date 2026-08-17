from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.functions import TruncMonth
from django.db.models import Count
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import os
from main.models import Commande, AffectationAnalyste, Rapport, ValidationRapport, SuiviCommande, Notification, MailInfo
from datetime import timedelta
from main.serializers import CommandeSerializer, RapportSerializer
from rest_framework.permissions import IsAuthenticated

User = get_user_model()

# Utility function for notifications and tracking
def create_notification_and_suivi(commande, user, action_type, message, status=None):
    """Fonction utilitaire pour créer une notification et un suivi."""
    Notification.objects.create(
        user=user,
        type=action_type,
        message=message
    )
    SuiviCommande.objects.create(
        commande=commande,
        user=user,
        type=action_type,
        action=message,
        commentaire=message
    )
    if status:
        commande.status = status
        commande.save()

# --- Vue pour la validation d'un rapport (mise à jour) ---
class ValidationRapportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, format=None):
        rapport = get_object_or_404(Rapport, pk=pk)
        validateur = request.user
        
        # Check if user is a validateur
        if validateur.role != 'Validateur':
            return Response({"detail": "Vous n'avez pas la permission d'effectuer cette action."}, status=status.HTTP_403_FORBIDDEN)
            
        status_validation = request.data.get('status')
        commentaire = request.data.get('commentaire')
        
        if status_validation not in ['valide', 'a_corriger']:
            return Response({"detail": "Statut de validation invalide."}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            validation, created = ValidationRapport.objects.update_or_create(
                rapport=rapport,
                defaults={
                    'validateur': validateur,
                    'status': status_validation,
                    'commentaire': commentaire
                }
            )
            
            commande = rapport.commande
            
            if status_validation == 'valide':
                # Set the responsible validator on the order
                commande.validateur = validateur
                commande.status = 'rapport_valide'
                commande.save()
                
                message = f"Votre rapport pour la commande {commande.notre_ref} a été validé."
                create_notification_and_suivi(
                    commande, rapport.analyste, 'VALIDATION', message, status='rapport_valide'
                )
                
            elif status_validation == 'a_corriger':
                # The order status goes back to 'in progress' for correction
                commande.status = 'en_cours'
                commande.save()
                
                message = f"Des corrections sont demandées pour votre rapport de la commande {commande.notre_ref}. Commentaires: {commentaire}"
                create_notification_and_suivi(
                    commande, rapport.analyste, 'CORRECTION', message, status='en_cours'
                )
        
        return Response({"detail": "Statut de validation mis à jour."}, status=status.HTTP_200_OK)

# --- NEW VIEW: Send Report to Client ---
class EnvoyerRapportClientAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, format=None):
        commande = get_object_or_404(Commande, pk=pk)
        
        # Security check: only the responsible validator or a Root user can send the report
        if request.user.role not in ['Root'] and commande.validateur != request.user:
            return Response({"detail": "Vous n'êtes pas autorisé à envoyer ce rapport."}, status=status.HTTP_403_FORBIDDEN)
        
        # Check if the report has already been sent
        if commande.email_envoye:
            return Response({"detail": "Le rapport a déjà été envoyé au client."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the report is in a valid state to be sent
        if commande.status != 'rapport_valide':
            return Response({"detail": "La commande n'est pas dans un état valide pour l'envoi au client."}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            # Update order status and new fields
            commande.status = 'envoye_client'
            commande.date_envoi_client = timezone.now()
            commande.email_envoye = True
            commande.save()
            
            # TODO: Add the logic to actually send the email with the attached report here.
            # This should ideally be an asynchronous task (e.g., Celery) to avoid blocking the API response.
            
            # Notification and tracking
            message = f"Le rapport pour la commande {commande.notre_ref} a été envoyé au client."
            create_notification_and_suivi(
                commande, request.user, 'ENVOI_CLIENT', message, status='envoye_client'
            )
            
        return Response({"detail": "Rapport envoyé au client avec succès."}, status=status.HTTP_200_OK)


# ─── Workflow validation rapport ───────────────────────────────────────────────

class SoumettreRapportValidationAPIView(APIView):
    """POST — Analyste soumet le rapport pour validation."""
    permission_classes = [IsAuthenticated]

    def post(self, request, commande_id):
        user = request.user
        if user.role != 'Analyste':
            return Response({"detail": "Réservé aux analystes."}, status=status.HTTP_403_FORBIDDEN)

        commande = get_object_or_404(Commande, pk=commande_id)

        if not AffectationAnalyste.objects.filter(commande=commande, analyste=user).exists():
            return Response({"detail": "Vous n'êtes pas affecté à cette commande."}, status=status.HTTP_403_FORBIDDEN)

        if commande.status != 'en_cours':
            return Response({"detail": f"La commande doit être en cours (statut actuel : {commande.status})."}, status=status.HTTP_400_BAD_REQUEST)

        rapport = Rapport.objects.filter(commande=commande).order_by('-date_soumission').first()
        if not rapport or not rapport.fichier:
            return Response({"detail": "Aucun fichier rapport n'a été déposé pour cette commande."}, status=status.HTTP_400_BAD_REQUEST)

        nom_analyste = user.get_full_name() or user.username
        msg = (
            f"Le rapport pour la commande {commande.notre_ref} a été soumis pour validation "
            f"par {nom_analyste}."
        )

        with transaction.atomic():
            commande.status = 'rapport_soumis'
            commande.save(update_fields=['status'])

            SuiviCommande.objects.create(
                commande=commande,
                user=user,
                type='SOUMISSION',
                action=msg,
                commentaire='',
            )

            destinataires = User.objects.filter(
                Q(role='Validateur') | Q(role='Root'),
                pays=commande.pays,
            ).exclude(pk=user.pk)

            for dest in destinataires:
                Notification.objects.create(user=dest, type='RAPPORT_SOUMIS', message=msg)
                if dest.email:
                    try:
                        send_mail(
                            subject=f"[BUCREP] Rapport soumis — {commande.notre_ref}",
                            message=msg,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[dest.email],
                            fail_silently=True,
                        )
                    except Exception:
                        pass

        return Response({"detail": "Rapport soumis pour validation.", "status": "rapport_soumis"}, status=status.HTTP_200_OK)


class RapportPreviewAPIView(APIView):
    """GET — Sert le PDF du rapport en lecture seule (inline, non téléchargeable)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, commande_id):
        commande = get_object_or_404(Commande, pk=commande_id)
        user = request.user

        is_analyste_affecte = (
            user.role == 'Analyste'
            and AffectationAnalyste.objects.filter(commande=commande, analyste=user).exists()
        )
        # Root : accès global. Validateur : limité à son pays.
        is_validateur_root = user.role in ['Validateur', 'Root'] and (
            user.role == 'Root' or user.pays_id == commande.pays_id
        )

        if not (is_analyste_affecte or is_validateur_root):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

        if commande.status not in ['rapport_soumis', 'rapport_valide', 'envoye_client', 'terminee']:
            return Response({"detail": "Aucun rapport soumis pour cette commande."}, status=status.HTTP_400_BAD_REQUEST)

        rapport = Rapport.objects.filter(commande=commande).order_by('-date_soumission').first()
        if not rapport or not rapport.fichier:
            return Response({"detail": "Fichier rapport introuvable."}, status=status.HTTP_404_NOT_FOUND)

        try:
            file_obj = rapport.fichier.open('rb')
            response = FileResponse(file_obj, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="rapport_{commande.notre_ref}.pdf"'
            response['X-Frame-Options'] = 'SAMEORIGIN'
            return response
        except (FileNotFoundError, OSError):
            return Response({"detail": "Fichier introuvable sur le serveur."}, status=status.HTTP_404_NOT_FOUND)


class RapportInfoAPIView(APIView):
    """GET — Retourne les métadonnées du rapport pour une commande."""
    permission_classes = [IsAuthenticated]

    def get(self, request, commande_id):
        commande = get_object_or_404(Commande, pk=commande_id)
        rapport = Rapport.objects.filter(commande=commande).select_related('analyste').order_by('-date_soumission').first()

        validation = None
        if rapport:
            try:
                v = rapport.validationrapport
                validation = {
                    'status': v.status,
                    'validateur': v.validateur.get_full_name() or v.validateur.username if v.validateur else None,
                    'commentaire': v.commentaire,
                    'date_validation': v.date_validation.isoformat() if v.date_validation else None,
                }
            except Exception:
                pass

        return Response({
            'commande_status': commande.status,
            'has_rapport': rapport is not None and bool(rapport.fichier),
            'rapport_id': rapport.pk if rapport else None,
            'analyste': rapport.analyste.get_full_name() or rapport.analyste.username if rapport and rapport.analyste else None,
            'date_soumission': rapport.date_soumission.isoformat() if rapport else None,
            'validation': validation,
        })


class ValiderRapportAPIView(APIView):
    """POST — Validateur ou Root valide le rapport d'une commande."""
    permission_classes = [IsAuthenticated]

    def post(self, request, commande_id):
        user = request.user
        if user.role not in ['Validateur', 'Root']:
            return Response({"detail": "Réservé aux validateurs et administrateurs."}, status=status.HTTP_403_FORBIDDEN)

        commande = get_object_or_404(Commande, pk=commande_id)

        # Validateur : limité à son pays. Root : accès global.
        if user.role == 'Validateur' and user.pays_id and user.pays_id != commande.pays_id:
            return Response({"detail": "Vous n'êtes pas habilité à valider les rapports de ce pays."}, status=status.HTTP_403_FORBIDDEN)

        if commande.status != 'rapport_soumis':
            return Response({"detail": "Ce rapport n'est pas en attente de validation."}, status=status.HTTP_400_BAD_REQUEST)

        rapport = Rapport.objects.filter(commande=commande).select_related('analyste').order_by('-date_soumission').first()
        if not rapport:
            return Response({"detail": "Aucun rapport trouvé pour cette commande."}, status=status.HTTP_404_NOT_FOUND)

        commentaire = request.data.get('commentaire', '')
        nom_validateur = user.get_full_name() or user.username

        with transaction.atomic():
            ValidationRapport.objects.update_or_create(
                rapport=rapport,
                defaults={
                    'validateur': user,
                    'status': 'valide',
                    'commentaire': commentaire,
                }
            )
            commande.status = 'rapport_valide'
            commande.validateur = user
            commande.save(update_fields=['status', 'validateur'])

            msg_validateur = f"Rapport validé par {nom_validateur}."
            if commentaire:
                msg_validateur += f" Commentaire : {commentaire}"
            SuiviCommande.objects.create(
                commande=commande,
                user=user,
                type='VALIDATION',
                action=msg_validateur,
                commentaire=commentaire,
            )

            msg_analyste = f"Votre rapport pour la commande {commande.notre_ref} a été validé par {nom_validateur}."
            Notification.objects.create(user=rapport.analyste, type='VALIDATION', message=msg_analyste)

        return Response({"detail": "Rapport validé avec succès.", "status": "rapport_valide"}, status=status.HTTP_200_OK)


class EnvoyerEmailRapportCommandeAPIView(APIView):
    """POST — Root ou Validateur envoie le rapport validé par email."""
    permission_classes = [IsAuthenticated]

    def post(self, request, commande_id):
        user = request.user
        if user.role not in ['Root', 'Validateur']:
            return Response({"detail": "Réservé aux administrateurs et validateurs."}, status=status.HTTP_403_FORBIDDEN)

        commande = get_object_or_404(Commande, pk=commande_id)

        # Validateur : limité à son pays. Root : accès global.
        if user.role == 'Validateur' and user.pays_id and user.pays_id != commande.pays_id:
            return Response({"detail": "Vous n'êtes pas habilité à agir sur les commandes de ce pays."}, status=status.HTTP_403_FORBIDDEN)

        if commande.status not in ['rapport_valide', 'envoye_client', 'terminee']:
            return Response({"detail": "Le rapport doit être validé avant envoi."}, status=status.HTTP_400_BAD_REQUEST)

        rapport = Rapport.objects.filter(commande=commande).order_by('-date_soumission').first()
        if not rapport or not rapport.fichier:
            return Response({"detail": "Aucun fichier rapport disponible pour cette commande."}, status=status.HTTP_404_NOT_FOUND)

        destinataire = (request.data.get('destinataire') or '').strip()
        sujet = (request.data.get('sujet') or f"Rapport de solvabilité — {commande.notre_ref}").strip()
        message_perso = (request.data.get('message_personnalise') or '').strip()
        cc_raw = (request.data.get('cc_emails') or '').strip()

        if not destinataire:
            return Response({"detail": "L'adresse email du destinataire est requise."}, status=status.HTTP_400_BAD_REQUEST)

        cc_list = [e.strip() for e in cc_raw.replace(',', ';').split(';') if e.strip()]

        expediteur_nom = user.get_full_name() or user.username
        raison_sociale = getattr(commande, 'raison_sociale', None) or str(commande)
        pays_nom = str(commande.pays) if getattr(commande, 'pays', None) else None
        type_rapport_val = getattr(commande, 'type_rapport', None)

        html_content = render_to_string('main/emails/email_rapport_valide.html', {
            'destinataire_nom': destinataire.split('@')[0].replace('.', ' ').replace('_', ' ').capitalize(),
            'body': message_perso or f"Veuillez trouver en pièce jointe le rapport de solvabilité pour la commande {commande.notre_ref}.",
            'titre1': commande.notre_ref,
            'titre2': raison_sociale,
            'titre3': f"{type_rapport_val or 'Standard'} — {pays_nom or ''}".strip(' —'),
            'expediteur_nom': expediteur_nom,
            'date_envoi': timezone.now(),
        })

        texte_brut = (
            f"Bonjour,\n\n"
            f"Veuillez trouver en pièce jointe le rapport de solvabilité pour la commande {commande.notre_ref}.\n\n"
            f"Entreprise : {raison_sociale}\n"
            f"Référence  : {commande.notre_ref}\n\n"
            f"{'Message : ' + message_perso + chr(10) + chr(10) if message_perso else ''}"
            f"Cordialement,\nL'équipe BUCREP / ACREMAC"
        )

        success = False
        err_msg = ''
        try:
            msg = EmailMultiAlternatives(
                subject=sujet,
                body=texte_brut,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[destinataire],
                cc=cc_list,
            )
            msg.attach_alternative(html_content, 'text/html')

            with rapport.fichier.open('rb') as f:
                pdf_bytes = f.read()
            filename = os.path.basename(rapport.fichier.name) or f"rapport_{commande.notre_ref}.pdf"
            msg.attach(filename, pdf_bytes, 'application/pdf')
            msg.send(fail_silently=False)
            success = True
        except Exception as exc:
            err_msg = str(exc)

        with transaction.atomic():
            mail_info = MailInfo.objects.create(
                user=user,
                subject=sujet,
                cc_emails=';'.join([destinataire] + cc_list),
                success=success,
                formats_generes={'to': destinataire, 'cc': cc_list},
            )
            mail_info.commands.add(commande)

            action_msg = (
                f"Email envoyé à {destinataire} — Sujet : {sujet}"
                if success else
                f"[ERREUR] Tentative d'envoi à {destinataire} — {err_msg}"
            )
            SuiviCommande.objects.create(
                commande=commande,
                user=user,
                type='ENVOI_CLIENT',
                action=action_msg,
                commentaire=message_perso,
            )

            if success and commande.status == 'rapport_valide':
                commande.status = 'envoye_client'
                commande.save(update_fields=['status'])

        if success:
            return Response({"detail": "Rapport envoyé avec succès.", "mail_info_id": mail_info.pk}, status=status.HTTP_200_OK)
        return Response({"detail": f"Erreur lors de l'envoi : {err_msg}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HistoriqueEmailsCommandeAPIView(APIView):
    """GET — Historique des envois email pour une commande."""
    permission_classes = [IsAuthenticated]

    def get(self, request, commande_id):
        user = request.user
        if user.role not in ['Root', 'Validateur']:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

        commande = get_object_or_404(Commande, pk=commande_id)

        if user.pays_id != commande.pays_id:
            return Response({"detail": "Accès refusé pour ce pays."}, status=status.HTTP_403_FORBIDDEN)

        mail_infos = (
            MailInfo.objects.filter(commands=commande)
            .select_related('user')
            .order_by('-date_sent')
        )

        results = []
        for mi in mail_infos:
            fg = mi.formats_generes or {}
            if isinstance(fg, dict):
                to_email = fg.get('to', '')
                cc_emails_list = fg.get('cc', [])
            else:
                to_email = ''
                cc_emails_list = []
            results.append({
                'id': mi.pk,
                'date_sent': mi.date_sent.isoformat(),
                'to': to_email,
                'cc': cc_emails_list,
                'subject': mi.subject or '',
                'success': mi.success,
                'sent_by': mi.user.get_full_name() or mi.user.username,
            })

        nb_success = sum(1 for r in results if r['success'])
        return Response({
            'count': len(results),
            'nb_success': nb_success,
            'nb_failed': len(results) - nb_success,
            'last_sent': results[0]['date_sent'] if results else None,
            'results': results,
        })


class ClientsAvecRapportAPIView(APIView):
    """
    GET — Liste tous les clients actifs (role=Client) sans filtre activation.
    URL : /api/orders/module/clients-rapport/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ['Root', 'Validateur']:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

        qs = User.objects.filter(
            role__iexact='Client',
            is_active=True,
        ).order_by('last_name', 'first_name', 'username')

        clients = []
        for c in qs:
            nom = ' '.join(filter(None, [c.first_name, c.last_name])) or c.username
            clients.append({
                'id': c.pk,
                'username': c.username,
                'nom': nom,
                'email': c.email or '',
            })

        return Response({'count': len(clients), 'data': clients})


class CommandesClientRapportAPIView(APIView):
    """
    GET — Commandes d'un client avec rapport_valide ou envoye_client,
    filtrées par période optionnelle.
    URL : /api/orders/module/clients-rapport/<client_id>/commandes/
    Params : periode = today | 7days | 30days | all (défaut)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        user = request.user
        if user.role not in ['Root', 'Validateur']:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

        periode = request.query_params.get('periode', 'all')
        qs = Commande.objects.filter(
            client_id=client_id,
            status__in=['rapport_valide', 'envoye_client', 'terminee'],
        ).select_related('acheteur', 'client', 'pays').order_by('-date_recept_commande')

        # Filtrer par pays actif (passé depuis le front) ou pays du Validateur
        pays_id_param = request.query_params.get('pays_id')
        if pays_id_param:
            try:
                qs = qs.filter(pays_id=int(pays_id_param))
            except (ValueError, TypeError):
                pass
        elif user.role == 'Validateur' and user.pays_id:
            qs = qs.filter(pays=user.pays)

        today = timezone.now().date()
        if periode == 'today':
            qs = qs.filter(date_recept_commande=today)
        elif periode == '7days':
            qs = qs.filter(date_recept_commande__gte=today - timedelta(days=7))
        elif periode == '30days':
            qs = qs.filter(date_recept_commande__gte=today - timedelta(days=30))

        data = []
        for c in qs:
            data.append({
                'id': c.pk,
                'notre_ref': c.notre_ref or '',
                'raison_sociale': c.raison_sociale or '',
                'type_rapport': c.type_rapport or '',
                'status': c.status,
                'date_recept_commande': c.date_recept_commande.isoformat() if c.date_recept_commande else None,
                'acheteur_id': c.acheteur_id,
                'acheteur_nom': c.acheteur.nom if c.acheteur else '',
                'email_envoye': c.email_envoye,
            })

        return Response({'count': len(data), 'data': data})


class GenererRapportCommandeAPIView(APIView):
    """
    POST — Génère un rapport PDF provisoire pour une commande qui n'en a pas encore.
    Utilise generate_pdf_report (ReportLab) et sauvegarde dans Rapport.fichier.
    URL : /api/orders/module/<id>/generer-rapport/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, commande_id):
        from io import BytesIO
        from django.core.files.base import ContentFile
        from main.api.views_api_emailling import generate_pdf_report

        user = request.user
        if user.role not in ['Root', 'Validateur']:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)

        commande = get_object_or_404(Commande, pk=commande_id)

        if user.role == 'Validateur' and user.pays_id and user.pays_id != commande.pays_id:
            return Response({"detail": "Accès non autorisé pour ce pays."}, status=status.HTTP_403_FORBIDDEN)

        rapport = Rapport.objects.filter(commande=commande).order_by('-date_soumission').first()
        if rapport and rapport.fichier:
            try:
                rapport.fichier.open('rb').close()
                return Response({"detail": "Un rapport PDF existe déjà.", "already_exists": True, "rapport_id": rapport.pk})
            except (FileNotFoundError, OSError):
                pass  # fichier manquant → régénérer

        pdf_bytes = generate_pdf_report(commande)

        if not rapport:
            rapport = Rapport(commande=commande, analyste=user)

        filename = f"rapport_{commande.notre_ref or commande.pk}.pdf".replace('/', '_')
        rapport.fichier.save(filename, ContentFile(pdf_bytes), save=True)

        return Response({
            "detail": "Rapport PDF généré avec succès.",
            "rapport_id": rapport.pk,
        })