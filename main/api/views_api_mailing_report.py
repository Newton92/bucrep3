from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db import transaction
import logging
import os
import json

from main.models import MailInfo, MailAttachment, Commande, Client, Document, SuiviCommande, Notification
from main.api.serializers_mailing_v2 import MailInfoDetailSerializer, EmailComposeSerializer
from main.api.views_reporting import generate_pdf_report, generate_html_report, generate_xml_report

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def envoyer_email_complet(request):
    """
    Endpoint unifié pour l'envoi d'emails avec toutes les fonctionnalités
    """
    try:
        serializer = EmailComposeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        user = request.user
        
        # 1. Récupérer les données
        client = Client.objects.get(id=data['client_id'])
        commandes = Commande.objects.filter(id__in=data['commandes_ids'])
        
        # 2. Créer l'enregistrement MailInfo
        mail_info = MailInfo.objects.create(
            user=user,
            subject=data['sujet'],
            cc_emails=data.get('cc', ''),
            formats_generes=data['formats'],
            custom_days=data.get('periode_jours'),
            success=False
        )
        mail_info.commands.set(commandes)
        
        # 3. Préparer les emails CC
        cc_list = []
        if data.get('cc'):
            cc_list = [email.strip() for email in data['cc'].split(';') if email.strip()]
        
        # Ajouter les emails des acheteurs si demandé
        if data.get('inclure_email_acheteur'):
            for commande in commandes:
                if commande.acheteur and commande.acheteur.email:
                    if commande.acheteur.email not in cc_list:
                        cc_list.append(commande.acheteur.email)
        
        # 4. Créer l'email
        email = EmailMultiAlternatives(
            subject=data['sujet'],
            body=data['message'],
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[client.email],
            cc=cc_list if cc_list else None
        )
        
        # Ajouter la version HTML si présente
        if data.get('html_message'):
            email.attach_alternative(data['html_message'], "text/html")
        
        # 5. Générer les rapports
        rapports_generes = []
        for commande in commandes:
            for format_type in data['formats']:
                try:
                    if format_type == 'pdf':
                        content = generate_pdf_report(commande)
                        filename = f"rapport_{commande.notre_ref or commande.id}.pdf"
                        content_type = 'application/pdf'
                    elif format_type == 'html':
                        content = generate_html_report(commande)
                        filename = f"rapport_{commande.notre_ref or commande.id}.html"
                        content_type = 'text/html'
                    elif format_type == 'xml':
                        content = generate_xml_report(commande)
                        filename = f"rapport_{commande.notre_ref or commande.id}.xml"
                        content_type = 'application/xml'
                    elif format_type == 'json':
                        content = json.dumps({'commande_id': commande.id}, indent=2).encode()
                        filename = f"rapport_{commande.notre_ref or commande.id}.json"
                        content_type = 'application/json'
                    else:
                        continue
                    
                    email.attach(filename, content, content_type)
                    rapports_generes.append(filename)
                    
                except Exception as e:
                    logger.error(f"Erreur génération rapport {commande.id} {format_type}: {str(e)}")
                    continue
        
        # 6. Ajouter les documents sélectionnés
        documents_attaches = []
        if data.get('documents_ids'):
            documents = Document.objects.filter(id__in=data['documents_ids'])
            for document in documents:
                try:
                    if document.fichier and os.path.exists(document.fichier.path):
                        with open(document.fichier.path, 'rb') as f:
                            content = f.read()
                            filename = os.path.basename(document.fichier.name)
                            email.attach(filename, content, 'application/octet-stream')
                            documents_attaches.append(filename)
                            
                            # Enregistrer dans MailAttachment
                            MailAttachment.objects.create(
                                mailinfo=mail_info,
                                upload=document.fichier,
                                file_name=filename,
                                file_size=document.fichier.size
                            )
                except Exception as e:
                    logger.error(f"Erreur document {document.id}: {str(e)}")
                    continue
        
        # 7. Ajouter les fichiers uploadés
        fichiers_uploades = []
        if request.FILES:
            for key, file in request.FILES.items():
                try:
                    content = file.read()
                    email.attach(file.name, content, file.content_type)
                    fichiers_uploades.append(file.name)
                    
                    MailAttachment.objects.create(
                        upload=file,
                        mailinfo=mail_info,
                        file_name=file.name,
                        file_size=file.size
                    )
                except Exception as e:
                    logger.error(f"Erreur fichier uploadé {file.name}: {str(e)}")
        
        # 8. ENVOYER L'EMAIL
        try:
            email.send()
            logger.info(f"Email envoyé avec succès à {client.email}")
            
            # Mettre à jour les commandes
            for commande in commandes:
                commande.status = 'envoye_client'
                commande.email_envoye = True
                commande.date_envoi_client = timezone.now()
                commande.save()
                
                # Créer un suivi
                SuiviCommande.objects.create(
                    commande=commande,
                    user=user,
                    action="Rapport envoyé par email",
                    type="ENVOI_CLIENT",
                    commentaire=f"Email envoyé à {client.email} avec {len(rapports_generes)} rapport(s)"
                )
            
            # Marquer le succès
            mail_info.success = True
            mail_info.save()
            
            # Créer une notification
            Notification.objects.create(
                user=user,
                type="ENVOI_CLIENT",
                message=f"Email envoyé à {client.nom} ({len(commandes)} commande(s))"
            )
            
            return Response({
                'success': True,
                'message': f'Email envoyé avec succès à {client.email}',
                'mail_id': mail_info.id,
                'stats': {
                    'commandes': commandes.count(),
                    'rapports': len(rapports_generes),
                    'documents': len(documents_attaches),
                    'fichiers_uploades': len(fichiers_uploades),
                    'cc': len(cc_list)
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur envoi SMTP: {str(e)}")
            mail_info.success = False
            mail_info.save()
            
            return Response({
                'success': False,
                'error': f'Erreur SMTP: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Client.DoesNotExist:
        return Response({'error': 'Client non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur générale: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historique_mails(request):
    """
    Récupère l'historique complet des emails avec pagination
    """
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        mails = MailInfo.objects.filter(user=request.user)\
                                .select_related('user')\
                                .prefetch_related('commands')\
                                .order_by('-date_sent')
        
        total = mails.count()
        mails_page = mails[start:end]
        
        serializer = MailInfoDetailSerializer(mails_page, many=True)
        
        return Response({
            'mails': serializer.data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detail_mail(request, mail_id):
    """
    Récupère les détails complets d'un email envoyé
    """
    try:
        mail = MailInfo.objects.get(id=mail_id, user=request.user)
        serializer = MailInfoDetailSerializer(mail)
        return Response(serializer.data)
    except MailInfo.DoesNotExist:
        return Response({'error': 'Mail non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def supprimer_mail(request, mail_id):
    """
    Supprime un email de l'historique (soft delete)
    """
    try:
        mail = MailInfo.objects.get(id=mail_id, user=request.user)
        mail.delete()  # Soft delete grâce à safedelete
        return Response({'success': True, 'message': 'Mail supprimé'})
    except MailInfo.DoesNotExist:
        return Response({'error': 'Mail non trouvé'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def renvoyer_mail(request, mail_id):
    """
    Renvoie un email précédemment envoyé
    """
    try:
        mail = MailInfo.objects.get(id=mail_id, user=request.user)
        
        # Récupérer les commandes et le client
        commandes = mail.commands.all()
        if not commandes.exists():
            return Response({'error': 'Aucune commande associée'}, status=400)
        
        # Trouver le client à partir de la première commande
        premiere_commande = commandes.first()
        if not premiere_commande.client:
            return Response({'error': 'Client non trouvé'}, status=404)
        
        client = premiere_commande.client
        
        # Reconstruire les données
        data = {
            'client_id': client.id,
            'commandes_ids': list(commandes.values_list('id', flat=True)),
            'sujet': mail.subject,
            'message': f"[RENVOI] {mail.subject}",
            'cc': mail.cc_emails,
            'formats': mail.formats_generes or ['pdf']
        }
        
        # Réutiliser la fonction d'envoi
        request.data = data
        return envoyer_email_complet(request)
        
    except MailInfo.DoesNotExist:
        return Response({'error': 'Mail non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def documents_par_commandes(request):
    """
    Récupère tous les documents des acheteurs associés aux commandes sélectionnées
    """
    try:
        commandes_ids = request.GET.get('commandes', '').split(',')
        commandes_ids = [int(id) for id in commandes_ids if id]
        
        if not commandes_ids:
            return Response({'documents': []})
        
        # Récupérer les acheteurs des commandes
        acheteurs_ids = Commande.objects.filter(
            id__in=commandes_ids,
            acheteur__isnull=False
        ).values_list('acheteur_id', flat=True).distinct()
        
        # Récupérer tous les documents de ces acheteurs
        documents = Document.objects.filter(
            acheteur_id__in=acheteurs_ids
        ).select_related('acheteur')
        
        documents_data = []
        for doc in documents:
            documents_data.append({
                'id': doc.id,
                'titre': doc.titre or 'Sans titre',
                'description': doc.description,
                'file_name': os.path.basename(doc.fichier.name) if doc.fichier else '',
                'file_url': doc.fichier.url if doc.fichier else '',
                'file_size': doc.fichier.size if doc.fichier else 0,
                'file_type': doc.fichier.name.split('.')[-1].lower() if doc.fichier else '',
                'acheteur_id': doc.acheteur.id,
                'acheteur_nom': doc.acheteur.nom,
                'created_at': doc.created_at.strftime('%d/%m/%Y'),
                'extension': doc.fichier.name.split('.')[-1].lower() if doc.fichier else ''
            })
        
        return Response({
            'documents': documents_data,
            'count': len(documents_data),
            'acheteurs_ids': list(acheteurs_ids)
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)