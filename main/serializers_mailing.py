# main/serializers_mailing.py
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Client, Commande, User, MailInfo, MailAttachment
from rest_framework import serializers
from main.models import Client, Commande, Document, MailInfo, MailAttachment
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework import serializers
from main.models import Client, Commande, Document, MailInfo, MailAttachment, Rapport, SuiviCommande
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone

class ClientSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = ['id', 'nom', 'email', 'telephone', 'nom_complet', 'date_inscription']
    
    def get_nom_complet(self, obj):
        return f"{obj.nom} - {obj.email}"

class CommandeSerializer(serializers.ModelSerializer):
    raison_sociale = serializers.CharField(read_only=True)
    notre_ref = serializers.CharField(read_only=True)
    date_recept_commande = serializers.DateField(read_only=True)
    
    # Champs pour l'acheteur
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_email = serializers.CharField(source='acheteur.email', read_only=True)
    acheteur_id = serializers.IntegerField(source='acheteur.id', read_only=True)  # AJOUTEZ CETTE LIGNE
    
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
            'acheteur_nom',
            'acheteur_email',
            'acheteur_id',  # AJOUTEZ CETTE LIGNE
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
    
    pays_nom = serializers.CharField(source='pays.nom', read_only=True)
    
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
            
            'pays_nom',
            
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



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
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

class EmailSendSerializerTwo(serializers.Serializer):
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
    
    
    
    
# Remplacer tout le EmailSendSerializer par celui-ci :
class EmailSendSerializer(serializers.Serializer):
    client_id = serializers.IntegerField(required=True)
    commandes = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1
    )
    formats = serializers.ListField(
        child=serializers.ChoiceField(choices=['pdf', 'html', 'xml']),
        required=True,
        min_length=1
    )
    sujet = serializers.CharField(required=True, max_length=500)
    message = serializers.CharField(required=True)
    cc = serializers.CharField(required=False, allow_blank=True)
    periode = serializers.CharField(required=False, allow_blank=True)
    nbre_days = serializers.IntegerField(required=False, min_value=1, max_value=365)
    
    def validate_cc(self, value):
        """Valider les emails en CC"""
        if value:
            emails = [email.strip() for email in value.split(';') if email.strip()]
            for email in emails:
                try:
                    validate_email(email)
                except ValidationError:
                    raise serializers.ValidationError(f"Email invalide: {email}")
        return value
    
    
    


class DocumentSerializer(serializers.ModelSerializer):
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 
            'titre', 
            'fichier', 
            'description',
            'file_name',
            'file_size',
            'file_type',
            'acheteur_id',
            'acheteur_nom',
            'created_at_formatted'
        ]
    
    def get_file_name(self, obj):
        if obj.fichier:
            return obj.fichier.name.split('/')[-1]
        return None
    
    def get_file_size(self, obj):
        if obj.fichier and hasattr(obj.fichier, 'size'):
            return obj.fichier.size
        return 0
    
    def get_file_type(self, obj):
        if obj.fichier:
            filename = obj.fichier.name
            extension = filename.split('.')[-1].lower() if '.' in filename else ''
            return extension
        return ''
    
    def get_created_at_formatted(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y')
        return None



class EmailSendDetailedSerializer(serializers.Serializer):
    client_id = serializers.IntegerField(required=True)
    commandes_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1
    )
    documents_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )
    period_type = serializers.ChoiceField(
        choices=['today', 'last_days', 'all'],
        required=True
    )
    custom_days = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=365
    )
    formats = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        min_length=1
    )
    cc_emails = serializers.CharField(required=False, allow_blank=True)
    sujet = serializers.CharField(required=True, max_length=500)
    message = serializers.CharField(required=True)
    fichiers_joints = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False),
        required=False,
        default=[]
    )
    
    def validate_cc_emails(self, value):
        """Valider le format des emails en CC"""
        if value:
            emails = [email.strip() for email in value.split(';') if email.strip()]
            for email in emails:
                try:
                    validate_email(email)
                except ValidationError:
                    raise serializers.ValidationError(f"Email invalide: {email}")
        return value
    
    def validate_formats(self, value):
        """Valider les formats"""
        allowed_formats = ['pdf', 'html', 'xml']
        for fmt in value:
            if fmt not in allowed_formats:
                raise serializers.ValidationError(f"Format non autorisé: {fmt}")
        return value

class MailHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    commands_details = CommandeDetailSerializer(source='commands', many=True, read_only=True)
    cc_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MailInfo
        fields = [
            'id', 'date_sent', 'user_name', 'subject',
            'success', 'commands_details', 'cc_emails', 'cc_count'
        ]
    
    def get_cc_count(self, obj):
        if obj.cc_emails:
            return len([e for e in obj.cc_emails.split(';') if e.strip()])
        return 0
    
    
    
class MailInfoSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    commands_details = CommandeDetailSerializer(source='commands', many=True, read_only=True)
    attachments_count = serializers.SerializerMethodField()
    cc_list = serializers.SerializerMethodField()
    
    class Meta:
        model = MailInfo
        fields = [
            'id', 'date_sent', 'user_name', 'subject',
            'success', 'commands_details', 'cc_emails', 
            'formats_generes', 'attachments_count', 'cc_list'
        ]
    
    def get_attachments_count(self, obj):
        return MailAttachment.objects.filter(mailinfo=obj).count()
    
    def get_cc_list(self, obj):
        if obj.cc_emails:
            return [email.strip() for email in obj.cc_emails.split(';') if email.strip()]
        return []