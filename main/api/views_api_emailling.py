from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import os

from main.models import Client, Commande, CustomUser, MailInfo, MailAttachment, SuiviCommande, Notification
from main.serializers_mailing import EmailSendSerializer, ClientSerializer, CommandeSerializer, MailInfoSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clients_autocomplete(request):
    query = request.GET.get('q', '')
    clients = Client.objects.filter(actif=True)
    
    if query:
        clients = clients.filter(
            Q(nom__icontains=query) | 
            Q(email__icontains=query)
        )[:20]
    else:
        clients = clients[:20]
    
    serializer = ClientSerializer(clients, many=True)
    return Response(serializer.data)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_commandes_by_client(request, client_id):
    try:
        client = Client.objects.get(id=client_id, actif=True)
        print(f"🔍 Recherche des commandes pour: {client.nom} ({client.email})")
    except Client.DoesNotExist:
        return Response(
            {'error': 'Client non trouvé'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # ESSAYER DIFFÉRENTES MÉTHODES DE FILTRAGE
    commandes_par_email = Commande.objects.filter(email=client.email)
    commandes_par_nom = Commande.objects.filter(raison_sociale__icontains=client.nom)
    
    print(f"📧 Par email: {commandes_par_email.count()} commandes")
    print(f"📋 Par nom: {commandes_par_nom.count()} commandes")
    
    # Utiliser l'une ou l'autre méthode, ou les combiner
    if commandes_par_email.exists():
        commandes = commandes_par_email
        print(f"✅ Utilisation du filtrage par email")
    elif commandes_par_nom.exists():
        commandes = commandes_par_nom
        print(f"✅ Utilisation du filtrage par nom")
    else:
        commandes = Commande.objects.none()
        print(f"❌ Aucune commande trouvée pour ce client")
    
    # FILTRAGE PAR PÉRIODE
    periode = request.GET.get('periode', 'all')
    today = timezone.now().date()
    
    if periode == 'today':
        commandes = commandes.filter(created_at__date=today)
        print(f"📅 Filtrage: Aujourd'hui ({today})")
    elif periode == '7days':
        start_date = today - timedelta(days=7)
        commandes = commandes.filter(created_at__date__gte=start_date)
        print(f"📅 Filtrage: 7 derniers jours ({start_date} à {today})")
    elif periode == 'month':
        commandes = commandes.filter(created_at__month=today.month, created_at__year=today.year)
        print(f"📅 Filtrage: Ce mois ({today.month}/{today.year})")
    else:
        print(f"📅 Filtrage: Toutes les périodes")
    
    print(f"📊 Résultat final: {commandes.count()} commande(s)")
    
    # DEBUG: Afficher les détails des premières commandes
    if commandes.exists():
        print("🐛 DEBUG des commandes trouvées:")
        for cmd in commandes[:3]:  # Afficher les 3 premières
            acheteur_info = f"{cmd.acheteur.nom} ({cmd.acheteur.email})" if cmd.acheteur else "Aucun"
            print(f"   - {cmd.notre_ref}:")
            print(f"     Raison sociale: {cmd.raison_sociale}")
            print(f"     Email: {cmd.email}")
            print(f"     Acheteur: {acheteur_info}")
            print(f"     Statut: {cmd.status}")
            print(f"     Créée le: {cmd.created_at}")
    
    # Serializer avec debug
    serializer = CommandeSerializer(commandes, many=True)
    
    # DEBUG des données serialisées
    print("📦 DEBUG données serialisées:")
    for i, data in enumerate(serializer.data[:2]):
        print(f"   Commande {i+1}:")
        print(f"     - notre_ref: {data.get('notre_ref')}")
        print(f"     - raison_sociale: {data.get('raison_sociale')}")
        print(f"     - acheteur_nom: {data.get('acheteur_nom')}")
        print(f"     - acheteur_email: {data.get('acheteur_email')}")
        print(f"     - date_recept_commande_formatted: {data.get('date_recept_commande_formatted')}")
        print(f"     - type_rapport: {data.get('type_rapport')}")
    
    return Response(serializer.data)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_rapports_email(request):
    serializer = EmailSendSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        data = serializer.validated_data
        client = Client.objects.get(id=data['client_id'])
        commandes = Commande.objects.filter(id__in=data['commandes_ids'])
        
        # Créer l'enregistrement MailInfo
        mail_info = MailInfo.objects.create(
            user=request.user,
            success=False
        )
        mail_info.commands.set(commandes)
        
        # Gérer les fichiers joints
        attachments = []
        for fichier in data.get('fichiers_joints', []):
            attachment = MailAttachment.objects.create(
                upload=fichier,
                mailinfo=mail_info
            )
            attachments.append(attachment)
        
        # Préparer l'email
        subject = data['sujet']
        message_text = data['message']
        
        # Gérer les emails en CC
        cc_list = []
        if data.get('cc_emails'):
            # Séparer les emails par point-virgule et nettoyer
            cc_emails = [email.strip() for email in data['cc_emails'].split(';') if email.strip()]
            # Valider le format des emails
            for email in cc_emails:
                try:
                    validate_email(email)
                    cc_list.append(email)
                except ValidationError:
                    # Ignorer les emails invalides
                    continue
        
        # Ajouter l'email de l'utilisateur courant en CC si configuré
        if request.user.email:
            cc_list.append(request.user.email)
        
        # Générer les rapports (à implémenter selon vos besoins)
        rapport_files = generate_rapports(commandes, data['formats'])
        
        # Envoyer l'email
        email = EmailMultiAlternatives(
            subject=subject,
            body=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[client.email],
            cc=cc_list if cc_list else None  # Ne pas mettre cc si liste vide
        )
        
        # Attacher les rapports générés
        for file_path in rapport_files:
            if os.path.exists(file_path):
                email.attach_file(file_path)
        
        # Attacher les fichiers joints supplémentaires
        for attachment in attachments:
            email.attach(
                attachment.upload.name,
                attachment.upload.read(),
                attachment.upload.content_type
            )
        
        # Envoyer l'email
        try:
            email.send()
            
            # Marquer le succès
            mail_info.success = True
            mail_info.save()
            
            # Mettre à jour les commandes
            for commande in commandes:
                commande.email_envoye = True
                commande.date_envoi_client = timezone.now()
                commande.save()
                
                # Créer un suivi
                SuiviCommande.objects.create(
                    commande=commande,
                    user=request.user,
                    action=f"Rapport envoyé au client par email",
                    type="ENVOI_CLIENT",
                    commentaire=f"Email envoyé à {client.email}" + 
                               (f", CC: {', '.join(cc_list)}" if cc_list else "")
                )
            
            # Créer une notification
            Notification.objects.create(
                user=request.user,
                type="ENVOI_CLIENT",
                message=f"Rapports envoyés avec succès à {client.nom}" +
                       (f" avec copie à {len(cc_list)} destinataire(s)" if cc_list else "")
            )
            
            return Response({
                'success': True,
                'message': 'Email envoyé avec succès',
                'cc_count': len(cc_list)
            })
            
        except Exception as e:
            # Marquer l'échec
            mail_info.success = False
            mail_info.save()
            
            return Response({
                'success': False,
                'error': f'Erreur lors de l\'envoi: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Client.DoesNotExist:
        return Response(
            {'error': 'Client non trouvé'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Erreur: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_email_history(request):
    """Récupérer l'historique des emails envoyés"""
    mails = MailInfo.objects.filter(user=request.user).order_by('-date_sent')
    serializer = MailInfoSerializer(mails, many=True)
    return Response(serializer.data)

def generate_rapports(commandes, formats):
    """
    Fonction pour générer les rapports dans différents formats
    À adapter selon votre logique de génération de rapports
    """
    generated_files = []
    
    for commande in commandes:
        for format in formats:
            # Implémentez ici votre logique de génération
            # Exemple: génération PDF, HTML, XML
            file_path = f"/tmp/rapport_{commande.id}.{format}"
            # ... logique de génération ...
            generated_files.append(file_path)
    
    return generated_files