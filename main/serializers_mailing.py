from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Client, Commande, CustomUser, MailInfo, MailAttachment

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'nom', 'email', 'telephone']

class CommandeSerializer(serializers.ModelSerializer):
    raison_sociale = serializers.CharField(read_only=True)
    notre_ref = serializers.CharField(read_only=True)
    date_recept_commande = serializers.DateField(read_only=True)
    
    # Champs pour l'acheteur
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_email = serializers.CharField(source='acheteur.email', read_only=True)
    
    # Dates formatées
    date_recept_commande_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Commande
        fields = [
            'id', 
            'notre_ref', 
            'raison_sociale', 
            'date_recept_commande',
            'date_recept_commande_formatted',
            'status', 
            'email_envoye',
            'acheteur_nom',     # Doit être inclus
            'acheteur_email',   # Doit être inclus
            'priorite',
            'type_rapport',
        ]
    
    def get_date_recept_commande_formatted(self, obj):
        if obj.date_recept_commande:
            return obj.date_recept_commande.strftime('%d/%m/%Y')
        return None
        
class CommandeDetailSerializer(serializers.ModelSerializer):
    raison_sociale = serializers.CharField(read_only=True)
    notre_ref = serializers.CharField(read_only=True)
    
    # Informations acheteur
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_email = serializers.CharField(source='acheteur.email', read_only=True)
    acheteur_id = serializers.IntegerField(source='acheteur.id', read_only=True)
    
    # Informations dates formatées
    date_recept_commande_formatted = serializers.SerializerMethodField()
    date_rapport_formatted = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    
    # Statut formaté
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Information crédit
    credit_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Commande
        fields = [
            'id', 
            'notre_ref', 
            'reference_client',
            'raison_sociale', 
            'date_recept_commande',
            'date_recept_commande_formatted',
            'date_rapport',
            'date_rapport_formatted',
            'created_at_formatted',
            'status',
            'status_display',
            'email_envoye',
            'priorite',
            'type_rapport',
            'delais',
            
            # Informations acheteur
            'acheteur_nom',
            'acheteur_email', 
            'acheteur_id',
            
            # Information crédit
            'credit_info',
        ]
    
    def get_date_recept_commande_formatted(self, obj):
        if obj.date_recept_commande:
            return obj.date_recept_commande.strftime('%d/%m/%Y')
        return None
    
    def get_date_rapport_formatted(self, obj):
        if obj.date_rapport:
            return obj.date_rapport.strftime('%d/%m/%Y')
        return None
    
    def get_created_at_formatted(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y à %H:%M')
        return None
    
    def get_credit_info(self, obj):
        if obj.credit_demande and obj.devise_credit_demande:
            return f"{obj.credit_demande} {obj.devise_credit_demande.code}"
        return "Non spécifié"



class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class MailAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailAttachment
        fields = ['id', 'upload', 'file_name']
    
    file_name = serializers.SerializerMethodField()
    
    def get_file_name(self, obj):
        return obj.upload.name.split('/')[-1] if obj.upload else ''

class MailInfoSerializer(serializers.ModelSerializer):
    commands_details = CommandeSerializer(source='commands', many=True, read_only=True)
    attachments = MailAttachmentSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = MailInfo
        fields = ['id', 'date_sent', 'user', 'user_name', 'commands', 
                 'commands_details', 'attachments', 'success']

class EmailSendSerializer(serializers.Serializer):
    client_id = serializers.IntegerField(required=True)
    commandes_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    formats = serializers.ListField(
        child=serializers.ChoiceField(choices=['pdf', 'html', 'xml']),
        required=True
    )
    sujet = serializers.CharField(max_length=255, required=True)
    message = serializers.CharField(required=True)
    fichiers_joints = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True
    )
    periode = serializers.ChoiceField(
        choices=[('today', 'Aujourd\'hui'), ('7days', '7 derniers jours'), 
                ('month', 'Ce mois'), ('all', 'Toutes')],
        required=True
    )