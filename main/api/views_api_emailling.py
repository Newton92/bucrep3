# main.api.views_api_emailling.py
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
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
import json

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

# main.models.py
from main.models import Client, Commande, User, MailInfo, MailAttachment, SuiviCommande, Notification, Acheteur, Document

# main.serializers_mailing.py
from main.serializers_mailing import EmailSendDetailedSerializer, CommandeDetailSerializer, MailInfoSerializer, MailHistorySerializer, DocumentSerializer
from main.serializers_mailing import EmailSendSerializer, ClientSerializer, CommandeSerializer, EmailSendDetailedSerializer, CommandeDetailSerializer, MailInfoSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
# Alternative sans l'import models
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.base import ContentFile
import os
import json
from io import BytesIO
from reportlab.pdfgen import canvas
from xhtml2pdf import pisa
import xml.etree.ElementTree as ET

# Import des modèles
from main.models import Client, Commande, User, MailInfo, MailAttachment, SuiviCommande, Notification, Rapport, Document

# Import des serializers
from main.serializers_mailing import EmailSendSerializer, ClientReportSerializer, DocumentSerializer, CommandeDetailSerializer, MailInfoSerializer


class ClientReportListView(APIView):
    """
    Vue pour lister les clients avec possibilité de recherche
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Récupérer le paramètre de recherche si présent
            search_query = request.GET.get('search', '')
            
            # Filtrer les clients actifs
            clients = User.objects.filter(role="Client")
            
            # Appliquer le filtre de recherche si spécifié
            if search_query and len(search_query) >= 3:
                clients = clients.filter(
                    Q(name__icontains=search_query) |  # Utilisez Q directement
                    Q(username__icontains=search_query) |  # Utilisez Q directement
                    Q(email__icontains=search_query)
                )
            
            # Limiter le nombre de résultats pour l'autocomplétion
            clients = clients.order_by('name')[:50]
            
            serializer = ClientReportSerializer(clients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClientListView(APIView):
    """
    Vue pour lister les clients avec possibilité de recherche
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Récupérer le paramètre de recherche si présent
            search_query = request.GET.get('search', '')
            
            # Filtrer les clients actifs
            clients = Client.objects.filter(actif=True)
            
            # Appliquer le filtre de recherche si spécifié
            if search_query and len(search_query) >= 3:
                clients = clients.filter(
                    Q(nom__icontains=search_query) |  # Utilisez Q directement
                    Q(email__icontains=search_query)
                )
            
            # Limiter le nombre de résultats pour l'autocomplétion
            clients = clients.order_by('nom')[:50]
            
            serializer = ClientSerializer(clients, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_client_commandes(request, client_id):
    """
    Récupérer les commandes d'un client pour une période donnée
    FILTRES : 
    1. Statut = "nouvelle" ou "en_cours"
    2. email_envoye = False (pas déjà envoyé)
    """
    try:
        periode = request.GET.get('periode', 'all')
        jours = int(request.GET.get('jours', 7))
        
        # Calculer la date de début selon la période
        now = timezone.now()
        
        if periode == 'today':
            date_debut = now.date()
        elif periode == '7days':
            date_debut = now.date() - timedelta(days=jours)
        elif periode == 'month':
            date_debut = now.date() - timedelta(days=30)
        else:
            date_debut = None
        
        # Filtrer les commandes avec statuts autorisés ET non envoyées
        commandes = Commande.objects.filter(
            client__id=client_id,
            status__in=['nouvelle', 'en_cours'],
            email_envoye=False  # Ajout de ce filtre
        )
        
        if date_debut:
            commandes = commandes.filter(created_at__gte=date_debut)
        
        # Limiter le nombre de résultats
        commandes = commandes.order_by('-created_at')[:100]
        
        serializer = CommandeSerializer(commandes, many=True)
        
        return Response({
            'commandes': serializer.data,
            'count': commandes.count(),
            'periode': periode,
            'jours': jours,
            'filter_info': {
                'status': ['nouvelle', 'en_cours'],
                'email_envoye': False,
                'message': 'Commandes non encore envoyées avec statut approprié'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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
def get_clients(request):
    """API pour récupérer la liste des clients (pour Select2)"""
    search = request.GET.get('search', '')
    clients = Client.objects.filter(actif=True)
    
    if search:
        clients = clients.filter(
            Q(nom__icontains=search) | 
            Q(email__icontains=search) |
            Q(telephone__icontains=search)
        )[:20]
    else:
        clients = clients[:10]
    
    data = []
    for client in clients:
        data.append({
            'id': client.id,
            'nom': client.nom,
            'email': client.email,
            'telephone': client.telephone,
            'adresse': client.adresse
        })
    
    return Response(data)





@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_commandes_by_client(request, client_id):
    """Récupérer les commandes avec filtrage amélioré"""
    try:
        client = Client.objects.get(id=client_id, actif=True)
    except Client.DoesNotExist:
        return Response({'error': 'Client non trouvé'}, status=404)
    
    # Récupérer les paramètres
    period_type = request.GET.get('period_type', 'today')
    custom_days = request.GET.get('custom_days', None)
    
    # Base queryset
    commandes = Commande.objects.filter(
        Q(email=client.email) | 
        Q(raison_sociale__icontains=client.nom)
    ).distinct()
    
    # Appliquer les filtres de période
    today = timezone.now().date()
    
    if period_type == 'today':
        commandes = commandes.filter(created_at__date=today)
    elif period_type == 'last_days':
        if custom_days:
            days = int(custom_days)
            start_date = today - timedelta(days=days)
            commandes = commandes.filter(created_at__date__gte=start_date)
        else:
            # Par défaut 7 jours
            start_date = today - timedelta(days=7)
            commandes = commandes.filter(created_at__date__gte=start_date)
    # 'all' - pas de filtre
    
    # Récupérer également les acheteurs pour les documents
    acheteurs_ids = commandes.filter(acheteur__isnull=False).values_list('acheteur_id', flat=True).distinct()
    
    serializer = CommandeDetailSerializer(commandes, many=True)
    
    return Response({
        'commandes': serializer.data,
        'acheteurs_ids': list(acheteurs_ids),
        'total': commandes.count()
    })
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_documents_by_acheteurs(request):
    """Récupérer les documents des acheteurs sélectionnés"""
    acheteurs_ids = request.GET.get('acheteurs_ids', '')
    
    if not acheteurs_ids:
        return Response({'documents': []})
    
    try:
        ids = [int(id) for id in acheteurs_ids.split(',') if id]
        documents = Document.objects.filter(acheteur_id__in=ids)
        serializer = DocumentSerializer(documents, many=True)
        return Response({'documents': serializer.data})
    except ValueError:
        return Response({'error': 'IDs invalides'}, status=400)
    
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_detailed_email(request):
    """Envoyer un email avec tous les détails"""
    serializer = EmailSendDetailedSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    data = serializer.validated_data
    
    try:
        client = Client.objects.get(id=data['client_id'])
        commandes = Commande.objects.filter(id__in=data['commandes_ids'])
        documents = Document.objects.filter(id__in=data.get('documents_ids', []))
        
        # Créer l'enregistrement MailInfo
        mail_info = MailInfo.objects.create(
            user=request.user,
            subject=data['sujet'],
            cc_emails=data.get('cc_emails', ''),
            formats_generes=data['formats'],
            custom_days=data.get('custom_days'),
            success=False
        )
        mail_info.commands.set(commandes)
        
        # Gestion des documents
        document_attachments = []
        for document in documents:
            attachment = MailAttachment.objects.create(
                upload=document.fichier,
                mailinfo=mail_info,
                is_document=True
            )
            document_attachments.append(attachment)
        
        # Gestion des fichiers joints supplémentaires
        for fichier in data.get('fichiers_joints', []):
            attachment = MailAttachment.objects.create(
                upload=fichier,
                mailinfo=mail_info,
                is_document=False
            )
        
        # Générer les rapports
        rapport_files = generate_rapports(commandes, data['formats'])
        
        # Préparer l'email
        email = EmailMultiAlternatives(
            subject=data['sujet'],
            body=data['message'],
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[client.email],
            cc=mail_info.get_cc_list()
        )
        
        # Attacher les rapports générés
        for file_path in rapport_files:
            if os.path.exists(file_path):
                email.attach_file(file_path)
        
        # Attacher les documents
        for attachment in MailAttachment.objects.filter(mailinfo=mail_info):
            with open(attachment.upload.path, 'rb') as f:
                email.attach(
                    os.path.basename(attachment.upload.name),
                    f.read(),
                    attachment.upload.content_type
                )
        
        # Envoyer l'email
        email.send()
        
        # Mettre à jour les commandes
        for commande in commandes:
            commande.email_envoye = True
            commande.date_envoi_client = timezone.now()
            commande.save()
        
        # Marquer le succès
        mail_info.success = True
        mail_info.save()
        
        return Response({
            'success': True,
            'message': f'Email envoyé avec succès à {client.email}',
            'mail_id': mail_info.id
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
        

    
    


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
        
        
        
        
# Dans main.api.views_api_emailling.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_email_history(request):
    """Récupérer l'historique des emails envoyés"""
    try:
        # Récupérer les mails de l'utilisateur
        mails = MailInfo.objects.filter(user=request.user).order_by('-date_sent')
        
        # Utiliser le serializer qui inclut les détails
        serializer = MailInfoSerializer(mails, many=True)
        
        return Response({
            'mails': serializer.data,
            'count': mails.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
        
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_email_history_version_2(request):
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




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_documents_by_acheteurs(request):
    """
    Récupérer les documents de plusieurs acheteurs
    Accepte une liste d'ID d'acheteurs séparés par des virgules
    """
    try:
        acheteurs_ids = request.GET.get('acheteurs', '')
        
        if not acheteurs_ids:
            return Response({
                'documents': [],
                'count': 0,
                'message': 'Aucun acheteur spécifié'
            }, status=status.HTTP_200_OK)
        
        # Convertir la chaîne en liste d'IDs
        acheteurs_ids_list = [int(id.strip()) for id in acheteurs_ids.split(',') if id.strip().isdigit()]
        
        if not acheteurs_ids_list:
            return Response({
                'error': 'Format d\'IDs invalide'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Récupérer les documents pour ces acheteurs
        documents = Document.objects.filter(acheteur_id__in=acheteurs_ids_list)
        
        # Optionnel: limiter les types de fichiers
        allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
        documents = [
            doc for doc in documents 
            if any(doc.fichier.name.lower().endswith(ext) for ext in allowed_extensions)
        ]
        
        serializer = DocumentSerializer(documents, many=True)
        
        return Response({
            'documents': serializer.data,
            'count': len(documents),
            'acheteurs_ids': acheteurs_ids_list,
            'message': f'{len(documents)} documents trouvés pour {len(acheteurs_ids_list)} acheteur(s)'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
        


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_acheteurs_from_commandes(request):
    """Récupérer les acheteurs des commandes sélectionnées"""
    commandes_ids = request.GET.get('commandes', '')
    
    if not commandes_ids:
        return Response({'acheteurs_ids': []})
    
    try:
        ids_list = [int(id.strip()) for id in commandes_ids.split(',') if id.strip()]
        commandes = Commande.objects.filter(id__in=ids_list, acheteur__isnull=False)
        acheteurs_ids = commandes.values_list('acheteur_id', flat=True).distinct()
        return Response({'acheteurs_ids': list(acheteurs_ids)})
    except ValueError:
        return Response({'error': 'IDs invalides'}, status=400)

        
        
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_acheteurs_by_commandes(request):
    """
    Récupérer les acheteurs associés à une liste de commandes
    """
    try:
        commandes_ids = request.GET.get('commandes', '')
        
        if not commandes_ids:
            return Response({
                'acheteurs': [],
                'acheteurs_ids': [],
                'count': 0
            }, status=status.HTTP_200_OK)
        
        # Convertir la chaîne en liste d'IDs
        commandes_ids_list = [int(id.strip()) for id in commandes_ids.split(',') if id.strip().isdigit()]
        
        # Récupérer les commandes avec leurs acheteurs
        commandes = Commande.objects.filter(
            id__in=commandes_ids_list
        ).select_related('acheteur')
        
        # Extraire les IDs des acheteurs uniques
        acheteurs_ids = list(set([c.acheteur.id for c in commandes if c.acheteur]))
        
        # Récupérer les informations des acheteurs
        acheteurs = Acheteur.objects.filter(id__in=acheteurs_ids).values('id', 'nom', 'email')
        
        return Response({
            'acheteurs': list(acheteurs),
            'acheteurs_ids': acheteurs_ids,
            'count': len(acheteurs_ids)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
        
        
        


from django.http import FileResponse, HttpResponse
from io import BytesIO
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import tempfile
import os
from datetime import datetime
import random

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_report(request):
    """
    Générer un rapport pour une commande
    Formats supportés: PDF, HTML, XML
    """
    try:
        # Récupérer les données de la requête
        data = request.data
        commande_id = data.get('commande_id')
        format_type = data.get('format')
        commande_ref = data.get('commande_ref', '')
        
        # Récupérer la commande
        commande = Commande.objects.get(id=commande_id)
        
        # Générer un nom de fichier unique
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_int = random.randint(1000, 9999)
        
        if format_type == 'pdf':
            filename = f"report_{commande_ref}_{timestamp}_{random_int}.pdf"
            content_type = 'application/pdf'
            file_content = generate_pdf_report(commande)
            
        elif format_type == 'html':
            filename = f"report_{commande_ref}_{timestamp}_{random_int}.html"
            content_type = 'text/html'
            file_content = generate_html_report(commande)
            
        elif format_type == 'xml':
            filename = f"report_{commande_ref}_{timestamp}_{random_int}.xml"
            content_type = 'application/xml'
            file_content = generate_xml_report(commande)
            
        else:
            return Response(
                {'error': 'Format non supporté'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer une réponse avec le fichier
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['X-Filename'] = filename
        response['X-File-Size'] = len(file_content)
        
        return response
        
    except Commande.DoesNotExist:
        return Response(
            {'error': 'Commande non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def generate_pdf_report(commande):
    """Générer un rapport PDF"""
    buffer = BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#2c3e50')
    )
    
    # Contenu du document
    story = []
    
    # Titre
    story.append(Paragraph("RAPPORT DE SOLVABILITÉ", title_style))
    story.append(Spacer(1, 12))
    
    # Informations de la commande
    commande_data = [
        ['Référence commande', commande.notre_ref or 'Non spécifiée'],
        ['Référence client', commande.reference_client or 'Non spécifiée'],
        ['Raison sociale', commande.raison_sociale],
        ['Date réception', commande.date_recept_commande.strftime('%d/%m/%Y') if commande.date_recept_commande else 'Non spécifiée'],
        ['Type rapport', commande.type_rapport],
        ['Statut', commande.get_status_display()],
    ]
    
    if commande.acheteur:
        commande_data.append(['Acheteur', commande.acheteur.nom])
        commande_data.append(['Email acheteur', commande.acheteur.email or 'Non spécifié'])
    
    if commande.credit_demande and commande.devise_credit_demande:
        commande_data.append(['Crédit demandé', f"{commande.credit_demande} {commande.devise_credit_demande.code}"])
    
    # Tableau des informations
    table = Table(commande_data, colWidths=[2*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#495057')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Section commentaires
    if commande.comments:
        story.append(Paragraph("Commentaires:", styles['Heading2']))
        story.append(Paragraph(commande.comments, styles['Normal']))
        story.append(Spacer(1, 12))
    
    # Pied de page
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Paragraph("ACREMAC - Service Rapports", styles['Italic']))
    
    # Générer le PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer.getvalue()

def generate_html_report(commande):
    """Générer un rapport HTML"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rapport de Solvabilité - {commande.notre_ref or 'Commande'}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .info-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            .info-table th {{
                background-color: #f8f9fa;
                text-align: left;
                padding: 10px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }}
            .info-table td {{
                padding: 10px;
                border: 1px solid #dee2e6;
            }}
            .section-title {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5px;
                margin-top: 30px;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                color: #6c757d;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>RAPPORT DE SOLVABILITÉ</h1>
            <p>ACREMAC - Service Rapports</p>
        </div>
        
        <h2 class="section-title">Informations de la commande</h2>
        <table class="info-table">
            <tr>
                <th>Référence commande</th>
                <td>{commande.notre_ref or 'Non spécifiée'}</td>
            </tr>
            <tr>
                <th>Référence client</th>
                <td>{commande.reference_client or 'Non spécifiée'}</td>
            </tr>
            <tr>
                <th>Raison sociale</th>
                <td>{commande.raison_sociale}</td>
            </tr>
            <tr>
                <th>Date de réception</th>
                <td>{commande.date_recept_commande.strftime('%d/%m/%Y') if commande.date_recept_commande else 'Non spécifiée'}</td>
            </tr>
            <tr>
                <th>Type de rapport</th>
                <td>{commande.type_rapport}</td>
            </tr>
            <tr>
                <th>Statut</th>
                <td>{commande.get_status_display()}</td>
            </tr>
    """
    
    if commande.acheteur:
        html_content += f"""
            <tr>
                <th>Acheteur</th>
                <td>{commande.acheteur.nom}</td>
            </tr>
            <tr>
                <th>Email acheteur</th>
                <td>{commande.acheteur.email or 'Non spécifié'}</td>
            </tr>
        """
    
    if commande.credit_demande and commande.devise_credit_demande:
        html_content += f"""
            <tr>
                <th>Crédit demandé</th>
                <td>{commande.credit_demande} {commande.devise_credit_demande.code}</td>
            </tr>
        """
    
    html_content += f"""
        </table>
    """
    
    if commande.comments:
        html_content += f"""
        <h2 class="section-title">Commentaires</h2>
        <p>{commande.comments}</p>
        """
    
    html_content += f"""
        <div class="footer">
            <p>Document généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            <p>ACREMAC │ We are committed to serve | We act with honesty & integrity</p>
            <p>© {datetime.now().year} ACREMAC - Tous droits réservés</p>
        </div>
    </body>
    </html>
    """
    
    return html_content.encode('utf-8')

def generate_xml_report(commande):
    """Générer un rapport XML"""
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<solvability_report>
    <metadata>
        <generated_date>{datetime.now().isoformat()}</generated_date>
        <generator>ACREMAC Report System</generator>
        <version>1.0</version>
    </metadata>
    
    <order_info>
        <reference>{commande.notre_ref or 'Not specified'}</reference>
        <client_reference>{commande.reference_client or 'Not specified'}</client_reference>
        <company_name>{commande.raison_sociale}</company_name>
        <reception_date>{commande.date_recept_commande.isoformat() if commande.date_recept_commande else ''}</reception_date>
        <report_type>{commande.type_rapport}</report_type>
        <status>{commande.status}</status>
        <status_display>{commande.get_status_display()}</status_display>
    </order_info>
    
    <buyer_info>
    """
    
    if commande.acheteur:
        xml_content += f"""
        <name>{commande.acheteur.nom}</name>
        <email>{commande.acheteur.email or 'Not specified'}</email>
        """
    else:
        xml_content += "<name>Not specified</name>"
    
    xml_content += """
    </buyer_info>
    
    <financial_info>
    """
    
    if commande.credit_demande and commande.devise_credit_demande:
        xml_content += f"""
        <requested_credit>
            <amount>{commande.credit_demande}</amount>
            <currency>{commande.devise_credit_demande.code}</currency>
        </requested_credit>
        """
    
    xml_content += """
    </financial_info>
    
    <additional_info>
    """
    
    if commande.comments:
        xml_content += f"""
        <comments>{commande.comments}</comments>
        """
    
    xml_content += """
    </additional_info>
    
    <system_info>
        <generation_timestamp>{datetime.now().timestamp()}</generation_timestamp>
        <report_id>ACR-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}</report_id>
    </system_info>
</solvability_report>
"""
    
    return xml_content.encode('utf-8')




# Dans main.api.views_api_emailling.py
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_email(request):
    """Envoyer un email avec toutes les pièces jointes - VERSION OPTIMISÉE"""
    import time
    start_time = time.time()
    
    try:
        print("=== DÉBUT ENVOI EMAIL ===")
        print(f"Temps: {time.strftime('%H:%M:%S')}")
        
        data = request.POST
        user = request.user
        
        # Vérifications minimales
        if not data.get('client_id'):
            return Response({'success': False, 'error': 'Client ID manquant'}, status=400)
        if not data.getlist('commandes'):
            return Response({'success': False, 'error': 'Aucune commande sélectionnée'}, status=400)
        
        # 1. Récupérer le client
        try:
            client = Client.objects.get(id=data['client_id'], actif=True)
            print(f"Client: {client.nom} ({client.email})")
        except Client.DoesNotExist:
            return Response({'success': False, 'error': 'Client non trouvé'}, status=404)
        
        # 2. Récupérer les commandes
        commandes_ids = data.getlist('commandes')
        commandes = Commande.objects.filter(id__in=commandes_ids)
        if not commandes.exists():
            return Response({'success': False, 'error': 'Aucune commande valide'}, status=400)
        
        print(f"Commandes: {commandes.count()}")
        
        # 3. Formats
        formats_list = data.getlist('formats', ['pdf'])  # Par défaut PDF
        
        # 4. Créer MailInfo
        mail_info = MailInfo.objects.create(
            user=user,
            subject=data.get('sujet', 'Rapports de solvabilité'),
            cc_emails=data.get('cc', ''),
            formats_generes=formats_list,
            success=False
        )
        mail_info.commands.set(commandes)
        
        # 5. Préparer l'email
        cc_list = []
        if data.get('cc'):
            cc_list = [email.strip() for email in data['cc'].split(';') if email.strip()]
        
        email = EmailMultiAlternatives(
            subject=mail_info.subject,
            body=data.get('message', ''),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[client.email],
            cc=cc_list if cc_list else None
        )
        
        # Ajouter la version HTML si disponible
        if 'html_message' in data and data['html_message']:
            email.attach_alternative(data['html_message'], "text/html")
        
        # 6. Générer les rapports (simplifié)
        rapports_crees = []
        for commande in commandes:
            for format_type in formats_list:
                try:
                    if format_type == 'pdf':
                        report_content = generate_pdf_report(commande)
                        filename = f"rapport_{commande.notre_ref or commande.id}.pdf"
                        content_type = 'application/pdf'
                    elif format_type == 'html':
                        report_content = generate_html_report(commande)
                        filename = f"rapport_{commande.notre_ref or commande.id}.html"
                        content_type = 'text/html'
                    elif format_type == 'xml':
                        report_content = generate_xml_report(commande)
                        filename = f"rapport_{commande.notre_ref or commande.id}.xml"
                        content_type = 'application/xml'
                    else:
                        continue
                    
                    email.attach(filename, report_content, content_type)
                    rapports_crees.append(filename)
                    
                except Exception as e:
                    print(f"Erreur rapport {commande.id} {format_type}: {str(e)}")
                    continue
        
        print(f"Rapports générés: {len(rapports_crees)}")
        
        # 7. Documents sélectionnés
        documents_attaches = []
        if 'documents_ids' in data:
            documents_ids = data.getlist('documents_ids')
            if documents_ids:
                documents = Document.objects.filter(id__in=documents_ids)
                print(f"Documents à attacher: {documents.count()}")
                
                for document in documents:
                    try:
                        if document.fichier and os.path.exists(document.fichier.path):
                            with open(document.fichier.path, 'rb') as f:
                                file_content = f.read()
                                filename = os.path.basename(document.fichier.name)
                                email.attach(filename, file_content, 'application/octet-stream')
                                documents_attaches.append(filename)
                                
                                MailAttachment.objects.create(
                                    mailinfo=mail_info,
                                    upload=document.fichier,
                                    file_name=filename,
                                    file_size=len(file_content),
                                    is_document=True,
                                    document=document
                                )
                    except Exception as e:
                        print(f"Erreur document {document.id}: {str(e)}")
                        continue
        
        # 8. Fichiers uploadés
        fichiers_joints = []
        if request.FILES:
            for key, file in request.FILES.items():
                try:
                    filename = file.name
                    file_content = file.read()
                    email.attach(filename, file_content, file.content_type)
                    fichiers_joints.append(filename)
                    
                    MailAttachment.objects.create(
                        upload=file,
                        mailinfo=mail_info,
                        file_name=filename,
                        file_size=file.size,
                        is_document=False
                    )
                except Exception as e:
                    print(f"Erreur fichier {filename}: {str(e)}")
        
        # 9. ENVOYER L'EMAIL
        print("Tentative d'envoi de l'email...")
        try:
            email.send()
            print("✓ Email envoyé avec succès")
            
            # Mettre à jour les commandes
            for commande in commandes:
                commande.status = 'envoye_client'
                commande.email_envoye = True
                commande.date_envoi_client = timezone.now()
                commande.save()
                
                SuiviCommande.objects.create(
                    commande=commande,
                    user=user,
                    action="Rapport envoyé par email",
                    type="ENVOI_CLIENT",
                    commentaire=f"Email envoyé à {client.email}"
                )
            
            # Succès
            mail_info.success = True
            mail_info.save()
            
            Notification.objects.create(
                user=user,
                type="ENVOI_CLIENT",
                message=f"Email envoyé à {client.nom}"
            )
            
            elapsed_time = time.time() - start_time
            print(f"=== FIN ENVOI RÉUSSI ===")
            print(f"Temps total: {elapsed_time:.2f} secondes")
            
            return Response({
                'success': True,
                'message': f'Email envoyé à {client.email}',
                'mail_id': mail_info.id,
                'commandes_count': commandes.count(),
                'formats': formats_list,
                'rapports_count': len(rapports_crees),
                'documents_count': len(documents_attaches),
                'fichiers_joints_count': len(fichiers_joints)
            })
            
        except Exception as e:
            print(f"✗ Erreur d'envoi: {str(e)}")
            mail_info.success = False
            mail_info.save()
            
            return Response({
                'success': False,
                'error': f'Erreur SMTP: {str(e)}'
            }, status=500)
            
    except Exception as e:
        print(f"✗ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        
        elapsed_time = time.time() - start_time
        print(f"=== FIN ENVOI ÉCHEC ===")
        print(f"Temps total: {elapsed_time:.2f} secondes")
        
        return Response({
            'success': False,
            'error': f'Erreur: {str(e)}'
        }, status=500)


def parse_cc_emails(cc_string):
    """Parser les emails en CC"""
    if not cc_string:
        return []
    
    emails = []
    for email in cc_string.split(';'):
        email = email.strip()
        if email:
            emails.append(email)
    
    return emails




        
        
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mail_details_version_2(request, mail_id):
    """Récupérer les détails d'un mail envoyé"""
    try:
        mail = MailInfo.objects.get(id=mail_id, user=request.user)
        serializer = MailHistorySerializer(mail)
        return Response(serializer.data)
    except MailInfo.DoesNotExist:
        return Response({'error': 'Mail non trouvé'}, status=404)





@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mail_details(request, mail_id):
    """Récupérer les détails d'un mail spécifique"""
    try:
        mail = MailInfo.objects.get(id=mail_id, user=request.user)
        serializer = MailInfoSerializer(mail)
        
        # Récupérer les pièces jointes
        attachments = MailAttachment.objects.filter(mailinfo=mail)
        attachments_data = []
        for att in attachments:
            attachments_data.append({
                'id': att.id,
                'name': att.upload.name.split('/')[-1],
                'url': att.upload.url if att.upload else '',
                'size': att.upload.size if att.upload else 0,
                'uploaded_at': att.upload.created if hasattr(att.upload, 'created') else None
            })
        
        return Response({
            'mail': serializer.data,
            'attachments': attachments_data
        })
        
    except MailInfo.DoesNotExist:
        return Response({'error': 'Mail non trouvé'}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request):
    """Marque une notification comme lue pour l'utilisateur courant."""
    notification_id = request.data.get("notification_id")
    if not notification_id:
        return Response(
            {"error": "notification_id est requis"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    updated = Notification.objects.filter(
        id=notification_id, user=request.user
    ).update(is_read=True)

    if updated == 0:
        return Response(
            {"error": "Notification introuvable"},
            status=status.HTTP_404_NOT_FOUND,
        )

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({"success": True, "unread_count": unread_count})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Marque toutes les notifications non lues de l'utilisateur comme lues."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({"success": True, "unread_count": 0})
