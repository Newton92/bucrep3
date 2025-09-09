from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
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
from main.models import Commande, AffectationAnalyste, Rapport, ValidationRapport, SuiviCommande, Notification
from main.serializers import CommandeSerializer, RapportSerializer
from rest_framework.permissions import IsAuthenticated

CustomUser = get_user_model()

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