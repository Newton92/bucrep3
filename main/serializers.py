# main/serializers.py
import decimal

from django.core.exceptions import ValidationError
from rest_framework import serializers

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from main.models import *
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from main.models import ScoringSansBilanAcheteur

# Vos serializers ici !


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "avatar",
            "code_secret",
            "address",
            "activation",
            "auth_a2f",
            "telephone",
            "profession",
            "email_cc",
        ]
        
        
        
# serializers.py
class ProfileUserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    password_changed_at = serializers.SerializerMethodField()
    last_login_formatted = serializers.SerializerMethodField()
    date_joined_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            "id", "username", "email", "first_name", "last_name", 
            "full_name", "avatar", "avatar_url", "telephone", 
            "profession", "address", "email_cc", "role",
            "last_login", "last_login_formatted",
            "date_joined", "date_joined_formatted",
            "password_changed_at"
        ]
        read_only_fields = ['id', 'username', 'role', 'last_login', 'date_joined']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        # Avatar par défaut avec initiales
        return None
    
    def get_full_name(self, obj):
        name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return name if name else obj.username
    
    def get_password_changed_at(self, obj):
        if hasattr(obj, 'password_changed_at') and obj.password_changed_at:
            return obj.password_changed_at.strftime('%d/%m/%Y %H:%M')
        return "Non défini"
    
    def get_last_login_formatted(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%d/%m/%Y %H:%M')
        return "Jamais connecté"
    
    def get_date_joined_formatted(self, obj):
        if obj.date_joined:
            return obj.date_joined.strftime('%d/%m/%Y %H:%M')
        return "Non défini"
    
    def validate_email(self, value):
        # Vérifier que l'email n'est pas déjà utilisé par un autre utilisateur
        user = self.instance
        if user and CustomUser.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def validate_telephone(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Le numéro de téléphone doit commencer par + (ex: +241...)")
        return value


class PaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pays
        fields = [
            "id",
            "nom",
            "code",
            "afficher_au_dashboard",
            "is_active",
            "date_creation",
            "date_modification",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pays
        fields = [
            "id",
            "nom",
        ]


class ProvinceSerializer(serializers.ModelSerializer):
    pays = PaysSerializer()  # Utilisez le sérialiseur pour inclure les détails du pays

    class Meta:
        model = Province
        fields = [
            "id",
            "nom",
            "code",
            "pays",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class AddProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = [
            "id",
            "nom",
            "code",
            "pays",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class UpdateProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = [
            "id",
            "nom",
            "code",
            "pays",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class VilleSerializer(serializers.ModelSerializer):
    province = (
        ProvinceSerializer()
    )  # Utilisez le sérialiseur pour inclure les détails du pays

    class Meta:
        model = Ville
        fields = [
            "id",
            "nom",
            "code",
            "province",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class VilleProvinceSerializer(serializers.ModelSerializer):
    province = (
        ProvinceSerializer()
    )  # Utilisez le sérialiseur pour inclure les détails du pays

    class Meta:
        model = Ville
        fields = [
            "id",
            "nom",
            "code",
            "province",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class AddVilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = [
            "id",
            "nom",
            "code",
            "province",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class UpdateVilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = [
            "id",
            "nom",
            "code",
            "province",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class AnneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annee
        fields = "__all__"  # Inclut tous les champs du modèle
        read_only_fields = [
            "date_creation",
            "date_modification",
        ]  # Ces champs seront uniquement en lecture


class DeviseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devise
        fields = "__all__"  # Inclut tous les champs du modèle
        read_only_fields = [
            "date_creation",
            "date_modification",
        ]  # Ces champs seront uniquement en lecture


class CouleurCommentaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouleurCommentaire
        fields = ["id", "couleur", "code"]


class AddCategoryNaceCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "poids", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class AddSubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoryNaceCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]



class CategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "poids", "created_at", "updated_at"]
        
        
class EditCategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "poids"]


class EditSubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    category = CategoryNaceCodeSerializer()

    class Meta:
        model = SubCategoryNaceCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    category = CategoryNaceCodeSerializer()

    class Meta:
        model = SubCategoryNaceCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "poids",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CategoryNaceCodeSerializer(serializers.ModelSerializer):
    #subcategories = SubCategoryNaceCodeSerializer(many=True, read_only=True)

    class Meta:
        model = CategoryNaceCode
        fields = [
            "id",
            "code",
            "libelle",
            "poids",
            "active",
            "created_at",
            "updated_at",
            #"subcategories",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AddSubCategoryNafCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoryNafCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "poids",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CategoryNafCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CategoryNafCode
        fields = [
            "id",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
            "subcategories",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SubCategoryNafCodeSerializer(serializers.ModelSerializer):
    category = CategoryNafCodeSerializer()

    class Meta:
        model = SubCategoryNafCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AddCategoryNafCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CategoryNafCode
        fields = ["id", "code", "libelle", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class CategoryNafCodeSerializer(serializers.ModelSerializer):
    subcategories = SubCategoryNafCodeSerializer(many=True, read_only=True)

    class Meta:
        model = CategoryNafCode
        fields = [
            "id",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
            "subcategories",
        ]
        read_only_fields = ["created_at", "updated_at"]


class EditSubCategoryNafCodeSerializer(serializers.ModelSerializer):
    category = CategoryNafCodeSerializer()

    class Meta:
        model = SubCategoryNafCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class FormeJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormeJuridique
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "poids",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]







class DomaineEntrepriseSerializer(serializers.ModelSerializer):

    class Meta:
        model = DomaineEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AddPosteEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosteEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "domaine",
            "active",
            "created_at",
            "updated_at",
        ]


class EditPosteEntrepriseSerializer(serializers.ModelSerializer):
    domaine = DomaineEntrepriseSerializer()

    class Meta:
        model = PosteEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "domaine",
            "active",
            "created_at",
            "updated_at",
        ]


class PosteEntrepriseSerializer(serializers.ModelSerializer):
    domaine = DomaineEntrepriseSerializer()

    class Meta:
        model = PosteEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "domaine",
            "active",
            "created_at",
            "updated_at",
        ]


class BaseModeleSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%d/%m/%Y")
    updated_at = serializers.DateTimeField(format="%d/%m/%Y")

    class Meta:
        fields = ["id", "code", "libelle", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ModeleRapportSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleRapport


class ModeleAlarmeSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleAlarme


class ModeleBilanSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleBilan


class ModeleBailSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleBail
        fields = "__all__"
        
        
class AddModeleBailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleBail
        fields = [
            "code",
            "libelle",
            "poids",
        ]

class EditModeleBailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleBail
        fields = [
            "id",
            "code",
            "libelle",
            "poids",
        ]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchModeleBailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleBail
        fields = "__all__"
        
        


class ModeleNotationSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleNotation


class ModeleAvisCommercialSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleAvisCommercial
        fields = "__all__"
        
        
class AddModeleAvisCommercialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAvisCommercial
        fields = [
            "code",
            "libelle",
            "poids",
        ]

class EditModeleAvisCommercialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAvisCommercial
        fields = [
            "id",
            "code",
            "libelle",
            "poids",
        ]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchModeleAvisCommercialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAvisCommercial
        fields = "__all__"
        
   







class ModeleRelationEntrepriseSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleRelationEntreprise


class ModeleInformationNotationEntrepriseSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleInformationNotationEntreprise


class ModeleComportementPaiementSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleComportementPaiement
        fields = "__all__"
        
        
class AddModeleComportementPaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementPaiement
        fields = [
            "code",
            "libelle",
            "poids",
        ]

class EditModeleComportementPaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementPaiement
        fields = [
            "id",
            "code",
            "libelle",
            "poids",
        ]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchModeleComportementPaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementPaiement
        fields = "__all__"
        
        
        
        





class ModeleComportementJugementSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleComportementJugement
              
class AddModeleModeleComportementJugementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementJugement
        fields = [
            "code",
            "libelle",
        ]

class EditModeleModeleComportementJugementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementJugement
        fields = [
            "id",
            "code",
            "libelle",
        ]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchModeleModeleComportementJugementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementJugement
        fields = "__all__"
        
     






class ModeleAgeSocieteSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleAgeSociete
        fields = "__all__"
              
class AddModeleAgeSocieteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAgeSociete
        fields = [
            "code",
            "libelle",
            "poids",
        ]

class EditModeleAgeSocieteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAgeSociete
        fields = [
            "id",
            "code",
            "libelle",
            "poids",
        ]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchModeleAgeSocieteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAgeSociete
        fields = "__all__"
        
        
        
        


class CategorieEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class StructureEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = StructureEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class StatutEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatutEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AcheteurSerializer(serializers.ModelSerializer):
    categorie_entreprise = CategorieEntrepriseSerializer()
    forme_juridique = FormeJuridiqueSerializer()
    statut_entreprise = StatutEntrepriseSerializer()

    pays = PaysSerializer()
    province = ProvinceSerializer()
    ville = VilleSerializer()

    class Meta:
        model = Acheteur
        fields = [
            "id",
            "code",
            "categorie_entreprise",
            "forme_juridique",
            "activite_principale",
            "nom",
            "sigle",
            "description",
            "date_creation",
            "statut_entreprise",
            "code_postal",
            "fax",
            "boite_postale",
            "email",
            "site_internet",
            "numero_adresse",
            "rue_adresse",
            "ville",
            "province",
            "pays",
            "couleur_commentaire",
            "commentaire",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# Ajoutez cette importation en haut du fichier
from django.db import transaction
from django.utils import timezone
import re
class DomainNameField(serializers.CharField):
    """Champ personnalisé pour les noms de domaine"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', 300)
        kwargs.setdefault('allow_blank', True)
        kwargs.setdefault('required', False)
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        """Convertir pour stockage"""
        if data:
            data = str(data).strip()
            # Supprimer https://
            data = re.sub(r'^https?://', '', data)
            # Supprimer slash final
            data = data.rstrip('/')
        return data
    
    def to_representation(self, value):
        """Convertir pour affichage"""
        if value:
            return f"https://{value}"
        return value

class AddAcheteurSerializer(serializers.ModelSerializer):
    # Utiliser notre champ personnalisé
    site_internet = DomainNameField()
    
    class Meta:
        model = Acheteur
        fields = [
            "id", "categorie_entreprise", "forme_juridique", 
            "activite_principale", "nom", "sigle", "description", 
            "date_creation", "statut_entreprise", "code_postal", 
            "fax", "boite_postale", "email", "site_internet", 
            "numero_adresse", "rue_adresse", "ville", "province", 
            "pays", "couleur_commentaire", "commentaire",
            "code"
        ]
        read_only_fields = ["created_at", "updated_at", "code"]
    
    def validate_site_internet(self, value):
        """Validation simple du site internet"""
        if value:
            value = value.strip()
            # Supprimer https:// si présent
            value = re.sub(r'^https?://', '', value)
            # Supprimer le slash final
            value = value.rstrip('/')
        return value
    
    def validate_email(self, value):
        """Validation de l'email"""
        if value:
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
                raise serializers.ValidationError("Format d'email invalide")
        return value
    
    def validate_nom(self, value):
        """Validation du nom"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Le nom doit contenir au moins 2 caractères")
        return value.strip()
    
    def validate_activite_principale(self, value):
        """Validation de l'activité principale"""
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("L'activité principale doit contenir au moins 3 caractères")
        return value.strip() if value else value
    
    def validate_commentaire(self, value):
        """Validation du commentaire"""
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("Le commentaire doit contenir au moins 10 caractères")
        return value.strip() if value else value
    
    def validate(self, data):
        """Validation globale"""
        # Vérifier la cohérence des dates
        date_creation = data.get('date_creation')
        if date_creation and date_creation > timezone.now().date():
            raise serializers.ValidationError({
                "date_creation": "La date de création ne peut pas être dans le futur"
            })
        
        # Vérifier la cohérence géographique
        ville = data.get('ville')
        province = data.get('province')
        pays = data.get('pays')
        
        if ville and province:
            if ville.province_id != province.id:
                raise serializers.ValidationError({
                    "ville": "La ville doit appartenir à la province sélectionnée"
                })
        
        if province and pays:
            if province.pays_id != pays.id:
                raise serializers.ValidationError({
                    "province": "La province doit appartenir au pays sélectionné"
                })
        
        # Générer un code automatique si non fourni
        if not data.get('code'):
            data['code'] = self.generate_code(data.get('nom'), data.get('pays'))
        
        return data
    
    def generate_code(self, nom, pays):
        """Génère un code unique pour l'acheteur"""
        from django.db.models import Max
        
        if not nom or not pays:
            return ""
        
        # Prendre les 3 premières lettres du nom
        prefix = nom[:3].upper()
        
        # Prendre le code du pays
        pays_code = pays.code if hasattr(pays, 'code') else 'GA'
        
        # Chercher le dernier numéro pour ce préfixe/pays
        last_code = Acheteur.objects.filter(
            code__startswith=f"ACH-{pays_code}-{prefix}"
        ).aggregate(max_num=Max('code'))
        
        if last_code['max_num']:
            try:
                last_num = int(last_code['max_num'].split('-')[-1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1
        
        return f"ACH-{pays_code}-{prefix}{next_num:04d}"
    
    @transaction.atomic
    def create(self, validated_data):
        """Création avec gestion des transactions et journalisation"""
        try:
            # Créer l'acheteur
            acheteur = super().create(validated_data)
            
            # Journaliser la création (ne pas bloquer en cas d'échec)
            try:
                request = self.context.get('request')
                if request and request.user:
                    from main.models import ActivityLog
                    
                    ActivityLog.objects.create(
                        user=request.user,
                        action_type='CREATE',  # ou 'ACHETEUR_CREATED'
                        object_id=acheteur.id,
                        object_type='Acheteur',
                        details=f"Création de l'acheteur '{acheteur.nom}' (ID: {acheteur.id})",
                        ip_address=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]  # Limiter la taille
                    )
            except Exception as log_error:
                # Log l'erreur mais ne pas bloquer la création
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Échec de journalisation: {str(log_error)}")
            
            return acheteur
            
        except Exception as e:
            raise serializers.ValidationError({
                "non_field_errors": f"Erreur lors de la création: {str(e)}"
            })    
            
            



from django.db import transaction
from rest_framework import serializers
import re

class EditAcheteurSerializer(serializers.ModelSerializer):
    site_internet = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=300,
        validators=[]  # DÉSACTIVER la validation Django
    )
    
    class Meta:
        model = Acheteur
        fields = [
            "id", "categorie_entreprise", "forme_juridique", 
            "activite_principale", "nom", "sigle", "description", 
            "date_creation", "statut_entreprise", "code_postal", 
            "fax", "boite_postale", "email", "site_internet", 
            "numero_adresse", "rue_adresse", "ville", "province", 
            "pays", "couleur_commentaire", "commentaire"
        ]
    
    def validate_site_internet(self, value):
        """Validation et nettoyage"""
        if not value:
            return ''
        
        value = str(value).strip()
        
        # Si c'est vide
        if not value:
            return ''
        
        # Supprimer les protocoles s'ils sont présents
        value = re.sub(r'^https?://', '', value)
        
        # Supprimer slash final
        value = value.rstrip('/')
        
        # Supprimer www. si présent
        value = re.sub(r'^www\.', '', value)
        
        # Retourner tel quel (Django URLField ajoutera https:// si nécessaire)
        return value.lower()
    
    def validate(self, data):
        """Validation globale"""
        # Nettoyer site_internet avant toutes les autres validations
        if 'site_internet' in data:
            data['site_internet'] = self.validate_site_internet(data['site_internet'])
        
        return data
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Mise à jour avec transactions - UNE SEULE MÉTHODE UPDATE"""
        try:
            # Journalisation optionnelle
            request = self.context.get('request')
            
            # Mettre à jour
            for field, value in validated_data.items():
                setattr(instance, field, value)
            
            # Nettoyer site_internet si nécessaire
            if hasattr(instance, 'site_internet') and instance.site_internet:
                # Si le site internet ne commence pas par http/https, ajouter https://
                if not instance.site_internet.startswith(('http://', 'https://')):
                    instance.site_internet = f'https://{instance.site_internet}'
            
            instance.save()
            
            # Log d'activité
            if request and request.user:
                from main.models import ActivityLog
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='UPDATE',
                    object_id=instance.id,
                    object_type='Acheteur',
                    details=f"Mise à jour de l'acheteur {instance.nom}",
                    ip_address=request.META.get('REMOTE_ADDR', '')
                )
            
            return instance
            
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': [f'Erreur lors de la mise à jour: {str(e)}']
            })


class GetAcheteurSerializer(serializers.ModelSerializer):
    categorie_entreprise = CategorieEntrepriseSerializer(read_only=True)
    forme_juridique = FormeJuridiqueSerializer(read_only=True)
    statut_entreprise = StatutEntrepriseSerializer(read_only=True)
    pays = PaysSerializer(read_only=True)
    province = ProvinceSerializer(read_only=True)
    ville = VilleSerializer(read_only=True)
    couleur_commentaire = CouleurCommentaireSerializer(read_only=True)
    
    # Formater le site_internet pour l'affichage
    site_internet_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Acheteur
        fields = [
            "id", "code", "categorie_entreprise", "forme_juridique",
            "activite_principale", "nom", "sigle", "description",
            "date_creation", "statut_entreprise", "code_postal",
            "fax", "boite_postale", "email", "site_internet",
            "site_internet_formatted", "numero_adresse", "rue_adresse",
            "ville", "province", "pays", "couleur_commentaire",
            "commentaire", "created_at", "updated_at"
        ]
        read_only_fields = fields
    
    def get_site_internet_formatted(self, obj):
        """Retourne l'URL formatée avec https://"""
        if obj.site_internet:
            return f"https://{obj.site_internet}"
        return None



class RiskRatingSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = RiskRating
        fields = "__all__"

    def validate_remboursabilite(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_situation_liquidite(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_performance_rentabilite(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_perspective_secteur(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_qualite_information_analyse(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_existence_garantie(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_terme_financier_duree_pret(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_mesure_propre_soutenir_credit(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value


class GetRiskRatingSerializer(serializers.ModelSerializer):

    acheteur = AcheteurSerializer()

    class Meta:
        model = RiskRating
        fields = "__all__"


class AddRiskRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskRating
        fields = [
            "id",
            "acheteur",
            "remboursabilite",
            "situation_liquidite",
            "performance_rentabilite",
            "perspective_secteur",
            "qualite_information_analyse",
            "existence_garantie",
            "terme_financier_duree_pret",
            "mesure_propre_soutenir_credit",
            "cotation_du_risque",
            "indice_du_risque",
            "interpretation",
            "analyse",
        ]
        

class EditRiskRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskRating
        fields = [
            "id",
            "acheteur",
            "remboursabilite",
            "situation_liquidite",
            "performance_rentabilite",
            "perspective_secteur",
            "qualite_information_analyse",
            "existence_garantie",
            "terme_financier_duree_pret",
            "mesure_propre_soutenir_credit",
            "cotation_du_risque",
            "indice_du_risque",
            "interpretation",
            "analyse",
        ]



# START MODEL RESUME

class ResumeSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    devise = DeviseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = Resume
        fields = "__all__"

    def validate_capital_social(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimale.")
        return value

    def validate_chiffre_affaire(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimale.")
        return value

    def validate_resultat_net(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_capitaux_propres(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimale.")
        return value

    def validate_nombre_employe(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimale.")
        return value


class AddResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            "id",
            "acheteur",
            "devise",
            "capital_social",
            "chiffre_affaire",
            "resultat_net",
            "capitaux_propre",
            "nombre_employe",
            "date_creation",
            "couleur_commentaire",
            "commentaire",
        ]


class GetResumeSerializer(serializers.ModelSerializer):

    acheteur = AcheteurSerializer()
    devise = DeviseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = Resume
        fields = "__all__"


class EditResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            "id",
            "acheteur",
            "devise",
            "capital_social",
            "chiffre_affaire",
            "resultat_net",
            "capitaux_propre",
            "nombre_employe",
            "date_creation",
            "couleur_commentaire",
            "commentaire",
        ]


class ResumeSerializer(serializers.ModelSerializer):
    """Serializer pour les opérations CRUD"""
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    devise_code = serializers.CharField(source='devise.code', read_only=True)
    couleur_code = serializers.CharField(source='couleur_commentaire.code', read_only=True)
    couleur_nom = serializers.CharField(source='couleur_commentaire.couleur', read_only=True)
    
    class Meta:
        model = Resume
        fields = [
            'id', 'acheteur', 'acheteur_nom',
            'devise', 'devise_code',
            'capital_social', 'chiffre_affaire', 'resultat_net',
            'capitaux_propre', 'nombre_employe', 'date_creation',
            'couleur_commentaire', 'couleur_code', 'couleur_nom',
            'commentaire', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'acheteur_nom']
    
    def validate(self, data):
        """Validation globale"""
        # Vérification cohérence des montants
        if (data.get('resultat_net') and data.get('chiffre_affaire') and 
            abs(data['resultat_net']) > abs(data['chiffre_affaire']) * 2):
            raise serializers.ValidationError({
                'resultat_net': "Le résultat net semble incohérent par rapport au chiffre d'affaires."
            })
        
        # Vérification de l'unicité
        if self.instance is None:  # Création
            if Resume.objects.filter(acheteur=data.get('acheteur')).exists():
                raise serializers.ValidationError({
                    'acheteur': "Un résumé existe déjà pour cet acheteur."
                })
        
        return data


class ResumeSummarySerializer(serializers.ModelSerializer):
    """Serializer léger pour l'affichage sommaire"""
    devise = serializers.CharField(source='devise.code')
    resultat_net_classe = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = [
            'capital_social', 'chiffre_affaire', 'resultat_net',
            'resultat_net_classe', 'capitaux_propre', 'nombre_employe',
            'devise', 'date_creation'
        ]
    
    def get_resultat_net_classe(self, obj):
        """Classe CSS en fonction du résultat net"""
        if obj.resultat_net is None:
            return 'neutral'
        return 'positive' if obj.resultat_net >= 0 else 'negative'

# END MODEL RESUME




class DonneesEnregistrementSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    forme_juridique_ref = FormeJuridiqueSerializer()
    statut_registre_ref = StatutEntrepriseSerializer()

    class Meta:
        model = DonneesEnregistrement
        fields = "__all__"


class GetDonneesEnregistrementSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = DonneesEnregistrement
        fields = "__all__"


class AddDonneesEnregistrementSerializer(serializers.ModelSerializer):
    # Remplacer le champ par défaut
    forme_juridique = serializers.CharField(required=False)
    statut_registre = serializers.CharField(required=False)
    class Meta:
        model = DonneesEnregistrement
        fields = [
            "id",
            "acheteur",
            "date_creation",
            "date_registre",
            "forme_juridique",
            "forme_juridique_ref",
            "numero_registre_commerce",
            "numero_fiscale",
            "statut_registre",
            "statut_registre_ref",
            "commentaire",
        ]


class EditDonneesEnregistrementSerializer(serializers.ModelSerializer):
    forme_juridique = serializers.CharField(required=False)
    statut_registre = serializers.CharField(required=False)
    forme_juridique_ref = serializers.PrimaryKeyRelatedField(
        queryset=FormeJuridique.objects.all(),
        required=False,
        allow_null=True,
        error_messages={
            'does_not_exist': 'La forme juridique sélectionnée n\'existe pas.',
            'incorrect_type': 'Veuillez fournir un ID numérique valide pour la forme juridique (ex: 16).'
        }
    )
    statut_registre_ref = serializers.PrimaryKeyRelatedField(
        queryset=StatutEntreprise.objects.all(),
        required=False,
        allow_null=True,
        error_messages={
            'does_not_exist': 'Le statut sélectionné n\'existe pas.',
            'incorrect_type': 'Veuillez fournir un ID numérique valide pour le statut (ex: 26).'
        }
    )

    class Meta:
        model = DonneesEnregistrement
        fields = [
            "id", "acheteur", "date_creation", "date_registre",
            "forme_juridique", "forme_juridique_ref",
            "numero_registre_commerce", "numero_fiscale",
            "statut_registre", "statut_registre_ref",
            "commentaire",
        ]

    def to_internal_value(self, data):
        # Créer une copie mutable des données
        data = data.copy()
        
        # Gérer l'inversion des champs
        # Si forme_juridique contient un ID numérique, le déplacer vers forme_juridique_ref
        if 'forme_juridique' in data and data['forme_juridique'] and data['forme_juridique'].isdigit():
            data['forme_juridique_ref'] = data['forme_juridique']
            # Conserver l'ancienne valeur textuelle dans forme_juridique si nécessaire
            # ou laisser vide car c'est un champ déprécié
            if 'forme_juridique_ref' in data and isinstance(data['forme_juridique_ref'], str):
                try:
                    # Essayer de trouver l'objet correspondant au texte
                    fj_obj = FormeJuridique.objects.filter(libelle__icontains=data['forme_juridique_ref']).first()
                    if fj_obj:
                        data['forme_juridique_ref'] = fj_obj.id
                    else:
                        # Si non trouvé, essayer de convertir en ID
                        try:
                            data['forme_juridique_ref'] = int(data['forme_juridique_ref'])
                        except (ValueError, TypeError):
                            pass
                except:
                    pass
        
        # Si forme_juridique_ref contient du texte, essayer de le convertir
        elif 'forme_juridique_ref' in data and isinstance(data['forme_juridique_ref'], str) and not data['forme_juridique_ref'].isdigit():
            try:
                # Essayer de trouver l'objet par le libellé
                fj_obj = FormeJuridique.objects.filter(libelle__icontains=data['forme_juridique_ref']).first()
                if fj_obj:
                    data['forme_juridique_ref'] = fj_obj.id
                else:
                    # Si non trouvé, essayer de le trouver dans l'ancien système de choix
                    for choice_key, choice_label in FORMEJURIDIQUE_CHOICES:
                        if choice_label == data['forme_juridique_ref']:
                            # Stocker dans l'ancien champ
                            data['forme_juridique'] = choice_label
                            # Laisser forme_juridique_ref vide
                            data['forme_juridique_ref'] = None
                            break
            except:
                pass
        
        # Même logique pour statut_registre
        if 'statut_registre' in data and data['statut_registre'] and data['statut_registre'].isdigit():
            data['statut_registre_ref'] = data['statut_registre']
        elif 'statut_registre_ref' in data and isinstance(data['statut_registre_ref'], str) and not data['statut_registre_ref'].isdigit():
            try:
                statut_obj = StatutEntreprise.objects.filter(libelle__icontains=data['statut_registre_ref']).first()
                if statut_obj:
                    data['statut_registre_ref'] = statut_obj.id
                else:
                    # Essayer de trouver dans l'ancien système
                    for choice_key, choice_label in LIEN_STATUT_CHOICE:
                        if choice_label == data['statut_registre_ref']:
                            data['statut_registre'] = choice_label
                            data['statut_registre_ref'] = None
                            break
            except:
                pass
        
        # Convertir les IDs en entiers si nécessaire
        if 'forme_juridique_ref' in data and isinstance(data['forme_juridique_ref'], str) and data['forme_juridique_ref'].isdigit():
            try:
                data['forme_juridique_ref'] = int(data['forme_juridique_ref'])
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'forme_juridique_ref': 'Veuillez fournir un ID numérique valide (ex: 16).'
                })

        if 'statut_registre_ref' in data and isinstance(data['statut_registre_ref'], str) and data['statut_registre_ref'].isdigit():
            try:
                data['statut_registre_ref'] = int(data['statut_registre_ref'])
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'statut_registre_ref': 'Veuillez fournir un ID numérique valide (ex: 26).'
                })

        return super().to_internal_value(data)








class TendanceSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    avis_commercial_ref = ModeleAvisCommercialSerializer()

    class Meta:
        model = Tendance
        fields = "__all__"


class GetTendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tendance
        fields = [
            'id', 'acheteur', 'avis_commercial', 'avis_commercial_ref',
            'presse_media', 'principaux_concurrent', 'commentaire',
            'created_at', 'updated_at'
        ]


class AddTendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tendance
        fields = [
            'acheteur', 'avis_commercial', 'avis_commercial_ref',
            'presse_media', 'principaux_concurrent', 'commentaire'
        ]


class EditTendanceSerializer(serializers.ModelSerializer):
    avis_commercial = serializers.CharField(required=False)
    avis_commercial_ref = serializers.PrimaryKeyRelatedField(
        queryset=ModeleAvisCommercial.objects.all(),
        required=False,
        allow_null=True,
        error_messages={
            'does_not_exist': 'L\'avis commercial sélectionné n\'existe pas.',
            'incorrect_type': 'Veuillez fournir un ID numérique valide pour l\'avis commercial.'
        }
    )

    class Meta:
        model = Tendance
        fields = [
            'avis_commercial', 'avis_commercial_ref',
            'presse_media', 'principaux_concurrent', 'commentaire'
        ]

    def to_internal_value(self, data):
        # Convertir les IDs en entiers si nécessaire
        if 'avis_commercial_ref' in data and isinstance(data['avis_commercial_ref'], str):
            try:
                data['avis_commercial_ref'] = int(data['avis_commercial_ref'])
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'avis_commercial_ref': 'Veuillez fournir un ID numérique valide.'
                })
        return super().to_internal_value(data)









class ResponsableAcheteurSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    poste_ref = PosteEntrepriseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = ResponsableAcheteur
        fields = "__all__"


class GetResponsableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponsableAcheteur
        fields = "__all__"


class AddResponsableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponsableAcheteur
        fields = [
            "id",
            "acheteur",
            "nom",
            "prenom",
            "sexe",
            "poste",
            "poste_ref",
            "nationalite",
            "couleur_commentaire",
            "commentaire",
        ]


class EditResponsableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponsableAcheteur
        fields = [
            "id",
            "acheteur",
            "nom",
            "prenom",
            "sexe",
            "poste",
            "poste_ref",
            "nationalite",
            "couleur_commentaire",
            "commentaire",
        ]


class AntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = AntecedantsJuridique
        fields = "__all__"


class GetAntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedantsJuridique
        fields = "__all__"


class AddAntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedantsJuridique
        fields = [
            "id",
            "acheteur",
            "dossier_faillite",
            "jugement_cour",
            "antecedant_redressement",
            "autre",
            "couleur_commentaire",
            "commentaire",
        ]


class EditAntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedantsJuridique
        fields = [
            "id",
            "acheteur",
            "dossier_faillite",
            "jugement_cour",
            "antecedant_redressement",
            "autre",
            "couleur_commentaire",
            "commentaire",
        ]


class RiskManagmentSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = RiskManagment
        fields = "__all__"


class GetRiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = "__all__"


class AddRiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = [
            "id",
            "acheteur",
            "professionalisme",
            "organisation",
            "turn_over",
            "greve",
            "degradation_qualite",
            "non_respect_condition",
            "couleur_commentaire",
            "commentaire",
        ]


class EditRiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = [
            "id",
            "acheteur",
            "professionalisme",
            "organisation",
            "turn_over",
            "greve",
            "degradation_qualite",
            "non_respect_condition",
            "couleur_commentaire",
            "commentaire",
        ]


class ConseilAdministrationSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    fonction_dans_le_conseil_ref = PosteEntrepriseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = ConseilAdministration
        fields = "__all__"


class GetConseilAdministrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConseilAdministration
        fields = "__all__"


class AddConseilAdministrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConseilAdministration
        fields = [
            "id",
            "acheteur",
            "nom",
            "fonction_dans_le_conseil",
            "fonction_dans_le_conseil_ref",
            "numero_adresse",
            "rue_adresse",
            "code_postale_adresse",
            "couleur_commentaire",
            "commentaire",
        ]


class EditConseilAdministrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConseilAdministration
        fields = [
            "id",
            "acheteur",
            "nom",
            "fonction_dans_le_conseil",
            "fonction_dans_le_conseil_ref",
            "numero_adresse",
            "rue_adresse",
            "code_postale_adresse",
            "couleur_commentaire",
            "commentaire",
        ]


class CompositionCapitalSocialSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    devise = DeviseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = CompositionCapitalSocial
        fields = "__all__"


class GetCompositionCapitalSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionCapitalSocial
        fields = "__all__"


class AddCompositionCapitalSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionCapitalSocial
        fields = [
            "id",
            "acheteur",
            "devise",
            "emis",
            "publie",
            "libere",
            "couleur_commentaire",
            "commentaire",
        ]


class EditCompositionCapitalSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionCapitalSocial
        fields = [
            "id",
            "acheteur",
            "devise",
            "emis",
            "publie",
            "libere",
            "couleur_commentaire",
            "commentaire",
        ]


class CompositionActionSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = CompositionAction
        fields = "__all__"


class GetCompositionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionAction
        fields = "__all__"


class AddCompositionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionAction
        fields = [
            "id",
            "acheteur",
            "nom",
            "prenom",
            "pourcentage",
            "couleur_commentaire",
            "commentaire",
        ]


class EditCompositionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionAction
        fields = [
            "id",
            "acheteur",
            "nom",
            "prenom",
            "pourcentage",
            "couleur_commentaire",
            "commentaire",
        ]






class OpinionCreditAcremacSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = OpinionCreditAcremac
        fields = "__all__"


class GetOpinionCreditAcremacSerializer(serializers.ModelSerializer):

    class Meta:
        model = OpinionCreditAcremac
        fields = "__all__"


class AddOpinionCreditAcremacSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpinionCreditAcremac
        fields = [
            "acheteur",
            "risque_de_defaut",
            "risque_de_concentration_credit",
            "risque_de_reputation",
            "risque_pays",
            "risque_de_taux_dinteret",
            "risque_de_liquidite",
            "risque_eleve",
            "risque_moyen",
            "risque_faible",
            "couleur_commentaire",
            "montant_credit_maximum",
            "commentaire",
        ]


class EditOpinionCreditAcremacSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpinionCreditAcremac
        fields = [
            "acheteur",
            "risque_de_defaut",
            "risque_de_concentration_credit",
            "risque_de_reputation",
            "risque_pays",
            "risque_de_taux_dinteret",
            "risque_de_liquidite",
            "risque_eleve",
            "risque_moyen",
            "risque_faible",
            "couleur_commentaire",
            "montant_credit_maximum",
            "commentaire",
        ]








class StructureSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()
    type_affiliation_ref = StructureEntrepriseSerializer()

    class Meta:
        model = Structure
        fields = "__all__"


class GetStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Structure
        fields = "__all__"


class AddStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Structure
        fields = [
            "acheteur",
            "nom",
            "type_affiliation",
            "type_affiliation_ref",
            "numero_adresse",
            "rue_adresse",
            "code_postale_adresse",
            "couleur_commentaire",
            "commentaire",
        ]


class EditStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Structure
        fields = [
            "acheteur",
            "nom",
            "type_affiliation",
            "type_affiliation_ref",
            "numero_adresse",
            "rue_adresse",
            "code_postale_adresse",
            "couleur_commentaire",
            "commentaire",
        ]


class AnalyseSectorielleSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = AnalyseSectorielle
        fields = "__all__"


class GetAnalyseSectorielleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseSectorielle
        fields = "__all__"


class AddAnalyseSectorielleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseSectorielle
        fields = ["acheteur", "couleur_commentaire", "commentaire", "impact_covid_19"]


class EditAnalyseSectorielleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseSectorielle
        fields = ["acheteur", "couleur_commentaire", "commentaire", "impact_covid_19"]


class CompteFinancierSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    type_bilan_ref = ModeleBilanSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = CompteFinancier
        fields = "__all__"


class GetCompteFinancierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancier
        fields = "__all__"


class AddCompteFinancierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancier
        fields = [
            "acheteur",
            "cabinet",
            "requis_pour_deposer",
            "credibilite_cabinet",
            "source",
            "presentation",
            "date_compte",
            "date_fin",
            "date_compte_n_moins_un",
            "date_fin_n_moins_un",
            "date_compte_n_moins_deux",
            "date_fin_n_moins_deux",
            "type_compte",
            "devise",
            "type_bilan",
            "type_bilan_ref",
            "couleur_commentaire",
            "commentaire",
        ]


class EditCompteFinancierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancier
        fields = [
            "acheteur",
            "cabinet",
            "requis_pour_deposer",
            "credibilite_cabinet",
            "source",
            "presentation",
            "date_compte",
            "date_fin",
            "date_compte_n_moins_un",
            "date_fin_n_moins_un",
            "date_compte_n_moins_deux",
            "date_fin_n_moins_deux",
            "type_compte",
            "devise",
            "type_bilan",
            "type_bilan_ref",
            "couleur_commentaire",
            "commentaire",
        ]


class OperationEtHistoriqueSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur

    class Meta:
        model = OperationEtHistorique
        fields = "__all__"


class GetOperationEtHistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationEtHistorique
        fields = "__all__"


class AddOperationEtHistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationEtHistorique
        fields = [
            "acheteur",
            "commentaire_ratios",
            "description_complete_activite",
            "importation",
            "historique",
        ]


class EditOperationEtHistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationEtHistorique
        fields = [
            "acheteur",
            "commentaire_ratios",
            "description_complete_activite",
            "importation",
            "historique",
        ]


class ProprieteEtActifSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    locaux_ref = (
        ModeleBailSerializer()
    )  # Utilisez un sérialiseur imbriqué pour la référence sur les locaux

    class Meta:
        model = ProprieteEtActif
        fields = "__all__"


class GetProprieteEtActifSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProprieteEtActif
        fields = "__all__"


class AddProprieteEtActifSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProprieteEtActif
        fields = ["acheteur", "locaux", "locaux_ref", "branche"]


class EditProprieteEtActifSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProprieteEtActif
        fields = ["acheteur", "locaux", "locaux_ref", "branche"]


class ConditionAchatSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur

    class Meta:
        model = ConditionAchat
        fields = "__all__"


class GetConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAchat
        fields = "__all__"


class AddConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAchat
        fields = ["acheteur", "local", "importation", "les_clients", "fournisseur"]


class EditConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAchat
        fields = ["acheteur", "local", "importation", "les_clients", "fournisseur"]


class ConditionDeVenteSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    recouvrement_de_dette_jugement_ref = ModeleComportementJugementSerializer()
    comportement_de_paiement_ref = ModeleComportementPaiementSerializer()

    class Meta:
        model = ConditionDeVente
        fields = "__all__"


class GetConditionDeVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionDeVente
        fields = "__all__"


class AddConditionDeVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionDeVente
        fields = [
            "acheteur",
            "local",
            "recouvrement_de_dette_jugement",
            "recouvrement_de_dette_jugement_ref",
            "comportement_de_paiement",
            "comportement_de_paiement_ref",
        ]


class EditConditionDeVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionDeVente
        fields = [
            "acheteur",
            "local",
            "recouvrement_de_dette_jugement",
            "recouvrement_de_dette_jugement_ref",
            "comportement_de_paiement",
            "comportement_de_paiement_ref",
        ]


class SommaireEtAvisSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = SommaireEtAvis
        fields = "__all__"


class GetSommaireEtAvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SommaireEtAvis
        fields = "__all__"


class AddSommaireEtAvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SommaireEtAvis
        fields = ["acheteur", "couleur_commentaire", "commentaire"]


class EditSommaireEtAvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SommaireEtAvis
        fields = ["acheteur", "couleur_commentaire", "commentaire"]


class AdviceSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur

    class Meta:
        model = Advice
        fields = "__all__"


class GetAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = "__all__"


class AddAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = [
            "acheteur",
            "points_forts",
            "points_faibles",
            "dynamisme_court_terme",
            "dynamisme_long_terme",
        ]


class EditAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = [
            "acheteur",
            "points_forts",
            "points_faibles",
            "dynamisme_court_terme",
            "dynamisme_long_terme",
        ]


class GeopoliticsSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur

    class Meta:
        model = Geopolitics
        fields = "__all__"


class GetGeopoliticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geopolitics
        fields = "__all__"


class AddGeopoliticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geopolitics
        fields = ["acheteur", "donnees_politiques", "donnees_economiques"]


class EditGeopoliticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geopolitics
        fields = ["acheteur", "donnees_politiques", "donnees_economiques"]


class BanquierSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    ville = VilleSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = Banquier
        fields = "__all__"


class GetBanquierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banquier
        fields = "__all__"


class AddBanquierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banquier
        fields = [
            "acheteur",
            "nom_banque",
            "numero_compte",
            "type_relation",
            "numero",
            "rue",
            "ville",
            "code_postal",
            "couleur_commentaire",
            "commentaire",
        ]


class EditBanquierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banquier
        fields = [
            "acheteur",
            "nom_banque",
            "numero_compte",
            "type_relation",
            "numero",
            "rue",
            "ville",
            "code_postal",
            "couleur_commentaire",
            "commentaire",
        ]


class ActifASerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ActifA
        fields = "__all__"

    def validate_biens_installations_equipements(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_inventaire(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_creances_commerciales_autres_creances(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_actif_impots_courant(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_caisses_banques(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value


class AddActifASerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifA
        fields = [
            "id",
            "annee",
            "acheteur",
            "biens_installations_equipements",
            "inventaire",
            "creances_commerciales_autres_creances",
            "actif_impots_courant",
            "caisses_banques",
            "created_by",
            "updated_by",
        ]


class GetActifASerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = ActifA
        fields = "__all__"


class EditActifASerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifA
        fields = [
            "id",
            "annee",
            "acheteur",
            "biens_installations_equipements",
            "inventaire",
            "creances_commerciales_autres_creances",
            "actif_impots_courant",
            "caisses_banques",
            "created_by",
            "updated_by",
        ]


class PassifASerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = PassifA
        fields = "__all__"

    def validate_capital_reserves(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_capital_declare(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_benefices_non_distribues(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_pret_bancaire(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_compte_courant_administrateurs(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dettes_commerciales_autres_dettes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_decouvert_bancaire(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_impots(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value


class AddPassifASerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifA
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital_reserves",
            "capital_declare",
            "benefices_non_distribues",
            "pret_bancaire",
            "compte_courant_administrateurs",
            "dettes_commerciales_autres_dettes",
            "decouvert_bancaire",
            "impots",
            "created_by",
            "updated_by",
        ]


class GetPassifASerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = PassifA
        fields = "__all__"


class EditPassifASerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifA
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital_reserves",
            "capital_declare",
            "benefices_non_distribues",
            "pret_bancaire",
            "compte_courant_administrateurs",
            "dettes_commerciales_autres_dettes",
            "decouvert_bancaire",
            "impots",
            "created_by",
            "updated_by",
        ]


class ResultatASerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ResultatA
        fields = "__all__"

    def validate_produits_activites_ordinaires(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ventes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_charges_exploitation(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_frais_vente_generaux_administratifs(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_revenus(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_frais_financier(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_charge_impot_sur_revenu(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_elements_resultat_global(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value


class AddResultatASerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatA
        fields = [
            "id",
            "annee",
            "acheteur",
            "produits_activites_ordinaires",
            "ventes",
            "charges_exploitation",
            "frais_vente_generaux_administratifs",
            "autres_revenus",
            "frais_financier",
            "charge_impot_sur_revenu",
            "autres_elements_resultat_global",
            "created_by",
            "updated_by",
        ]


class GetResultatASerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = ResultatA
        fields = "__all__"


class EditResultatASerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatA
        fields = [
            "id",
            "annee",
            "acheteur",
            "produits_activites_ordinaires",
            "ventes",
            "charges_exploitation",
            "frais_vente_generaux_administratifs",
            "autres_revenus",
            "frais_financier",
            "charge_impot_sur_revenu",
            "autres_elements_resultat_global",
            "created_by",
            "updated_by",
        ]


class ActifCSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ActifC
        fields = "__all__"

    def validate_capital_souscrit_non_app(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_frais_recherche_developpement(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_brevet_licence_logiciels(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_fonds_commercial(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_immobilisations_incorporelles(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_terrains(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_constructions(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_materiels_et_outils(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_materiel_de_transport(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_immos_corp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_immos_en_cours(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_avances_et_acptes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_participations(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_prets(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_mp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_encours_mp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_pf(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_encours_pf(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_encours_services(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_mses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_avances_acptes_verses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_clients_et_cptes_rattaches(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_creances(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_valeurs_a_encaisser(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_banques_cheques_postaux_caisse(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_cca(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_charges_a_repartir_et_frais_etablissement(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_primes_de_rbt(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_eca(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ene(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_effectif(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_amortissements(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_provisions_stocks(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_provisions_creances(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_provisions_vmp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value


class AddActifCSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifC
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital_souscrit_non_app",
            "frais_recherche_developpement",
            "brevet_licence_logiciels",
            "fonds_commercial",
            "autres_immobilisations_incorporelles",
            "terrains",
            "constructions",
            "materiels_et_outils",
            "materiel_de_transport",
            "autres_immos_corp",
            "immos_en_cours",
            "avances_et_acptes",
            "participations",
            "prets",
            "autres",
            "stocks_mp",
            "stocks_encours_mp",
            "stocks_pf",
            "stocks_encours_pf",
            "stocks_encours_services",
            "stocks_mses",
            "avances_acptes_verses",
            "clients_et_cptes_rattaches",
            "autres_creances",
            "valeurs_a_encaisser",
            "banques_cheques_postaux_caisse",
            "cca",
            "charges_a_repartir_et_frais_etablissement",
            "primes_de_rbt",
            "eca",
            "eene",
            "effectif",
            "amortissements",
            "provisions_stocks",
            "provisions_creances",
            "provisions_vmp",
            "created_by",
            "updated_by",
        ]


class GetActifCSerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = ActifC
        fields = "__all__"


class EditActifCSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifC
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital_souscrit_non_app",
            "frais_recherche_developpement",
            "brevet_licence_logiciels",
            "fonds_commercial",
            "autres_immobilisations_incorporelles",
            "terrains",
            "constructions",
            "materiels_et_outils",
            "materiel_de_transport",
            "autres_immos_corp",
            "immos_en_cours",
            "avances_et_acptes",
            "participations",
            "prets",
            "autres",
            "stocks_mp",
            "stocks_encours_mp",
            "stocks_pf",
            "stocks_encours_pf",
            "stocks_encours_services",
            "stocks_mses",
            "avances_acptes_verses",
            "clients_et_cptes_rattaches",
            "autres_creances",
            "valeurs_a_encaisser",
            "banques_cheques_postaux_caisse",
            "cca",
            "charges_a_repartir_et_frais_etablissement",
            "primes_de_rbt",
            "eca",
            "eene",
            "effectif",
            "amortissements",
            "provisions_stocks",
            "provisions_creances",
            "provisions_vmp",
            "created_by",
            "updated_by",
        ]


class PassifCSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = PassifC
        fields = "__all__"

    def validate_capital_social(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_primes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ecarts_de_reevaluation(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_reserve(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_report_a_nouveau(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_resultat_exercice(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_subv_invest(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_provision_regl(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_emprunts(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dette_credit_bail_contrat_assimile(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dettes_financiere_diverses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_provision_financiere_risque_charge(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dettes_fournisseurs_divers(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_avance_et_acomptes_recu(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dettes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dettes_fiscales_sociales(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_dettes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_banques_credit_escompte(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_banque_credit_caisse(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_banques_decouvert(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ecart_conversion_passif(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value


class AddPassifCSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifC
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital_social",
            "primes",
            "ecarts_de_reevaluation",
            "reserve",
            "report_a_nouveau",
            "resultat_exercice",
            "subv_invest",
            "provision_regl",
            "emprunts",
            "dette_credit_bail_contrat_assimile",
            "dettes_financiere_diverses",
            "provision_financiere_risque_charge",
            "dettes_fournisseurs_divers",
            "avance_et_acomptes_recu",
            "dettes",
            "dettes_fiscales_sociales",
            "autres_dettes",
            "banques_credit_escompte",
            "banque_credit_caisse",
            "banques_decouvert",
            "ecart_conversion_passif",
            "created_by",
            "updated_by",
        ]


class GetPassifCSerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = PassifC
        fields = "__all__"


class EditPassifCSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifC
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital_social",
            "primes",
            "ecarts_de_reevaluation",
            "reserve",
            "report_a_nouveau",
            "resultat_exercice",
            "subv_invest",
            "provision_regl",
            "emprunts",
            "dette_credit_bail_contrat_assimile",
            "dettes_financiere_diverses",
            "provision_financiere_risque_charge",
            "dettes_fournisseurs_divers",
            "avance_et_acomptes_recu",
            "dettes",
            "dettes_fiscales_sociales",
            "autres_dettes",
            "banques_credit_escompte",
            "banque_credit_caisse",
            "banques_decouvert",
            "ecart_conversion_passif",
            "created_by",
            "updated_by",
        ]


class ResultatCSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ResultatC
        fields = "__all__"

    def validate_vente_de_mdses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ventes_de_produits_fabriques(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_travaux_services_vendus(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_produit_accessoires(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_production_imblise(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_subventions_exploitations(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_production_stockee(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_reprises_de_provision(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_transferts_charges(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_produits(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_achat_mdses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_variation_stock_mdses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_achat_mp_autres_appro(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_var_stk_mp_app(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_achats(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_variation_de_stocks_autres_appro(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_transports(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_services_ext(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_impots_taxes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_charges_valeur_ajoutee(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_charges_personnel(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dotation_aux_amorts(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dotation_aux_provisions(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_charges_excedent_brute(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_revenus_fin_assimiles(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_prof_vmp_et_cre_actif_immo(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_interets_produit_assim(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_reprise_prov_et_transfert(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_diff_positive_de_change(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_prod_nets_cessions_vmp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dap(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_frais_fin_charges_assi(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_diff_negatives_de_change(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ch_nettes_cessions_vmp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_sur_op_gestion_prod_except(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_sur_op_en_capital_prod_except(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_reprise_prov_transfert(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_sur_op_gestion_charg_except(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_sur_op_en_capital_charg_except(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dap_et_transfert_charg_except(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value


class AddResultatCSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatC
        fields = [
            "id",
            "annee",
            "acheteur",
            "vente_de_mdses",
            "ventes_de_produits_fabriques",
            "travaux_services_vendus",
            "produit_accessoires",
            "production_imblise",
            "subventions_exploitations",
            "production_stockee",
            "reprises_de_provision",
            "transferts_charges",
            "autres_produits",
            "achat_mdses",
            "variation_stock_mdses",
            "achat_mp_autres_appro",
            "var_stk_mp_app",
            "autres_achats",
            "variation_de_stocks_autres_appro",
            "transports",
            "services_ext",
            "impots_taxes",
            "autres_charges_valeur_ajoutee",
            "charges_personnel",
            "dotation_aux_amorts",
            "dotation_aux_provisions",
            "autres_charges_excedent_brute",
            "revenus_fin_assimiles",
            "prof_vmp_et_cre_actif_immo",
            "interets_produit_assim",
            "reprise_prov_et_transfert",
            "diff_positive_de_change",
            "prod_nets_cessions_vmp",
            "dap",
            "frais_fin_charges_assi",
            "diff_negatives_de_change",
            "ch_nettes_cessions_vmp",
            "sur_op_gestion_prod_except",
            "sur_op_en_capital_prod_except",
            "reprise_prov_transfert",
            "sur_op_gestion_charg_except",
            "sur_op_en_capital_charg_except",
            "dap_et_transfert_charg_except",
            "participation_salairies",
            "impot_sur_benefices",
            "created_by",
            "updated_by",
        ]


class GetResultatCSerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = ResultatC
        fields = "__all__"


class EditResultatCSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatC
        fields = [
            "id",
            "annee",
            "acheteur",
            "vente_de_mdses",
            "ventes_de_produits_fabriques",
            "travaux_services_vendus",
            "produit_accessoires",
            "production_imblise",
            "subventions_exploitations",
            "production_stockee",
            "reprises_de_provision",
            "transferts_charges",
            "autres_produits",
            "achat_mdses",
            "variation_stock_mdses",
            "achat_mp_autres_appro",
            "var_stk_mp_app",
            "autres_achats",
            "variation_de_stocks_autres_appro",
            "transports",
            "services_ext",
            "impots_taxes",
            "autres_charges_valeur_ajoutee",
            "charges_personnel",
            "dotation_aux_amorts",
            "dotation_aux_provisions",
            "autres_charges_excedent_brute",
            "revenus_fin_assimiles",
            "prof_vmp_et_cre_actif_immo",
            "interets_produit_assim",
            "reprise_prov_et_transfert",
            "diff_positive_de_change",
            "prod_nets_cessions_vmp",
            "dap",
            "frais_fin_charges_assi",
            "diff_negatives_de_change",
            "ch_nettes_cessions_vmp",
            "sur_op_gestion_prod_except",
            "sur_op_en_capital_prod_except",
            "reprise_prov_transfert",
            "sur_op_gestion_charg_except",
            "sur_op_en_capital_charg_except",
            "dap_et_transfert_charg_except",
            "participation_salairies",
            "impot_sur_benefices",
            "created_by",
            "updated_by",
        ]


class ActifSysCohadaSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ActifS
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_frais_developpement_prospection(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddActifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = [
            "id",
            "annee",
            "acheteur",
            "frais_developpement_prospection",
            "brevets_licences_logiciels",
            "droits_propriete_commerciale_baux",
            "autres_immo_incorporelles",
            "terrains",
            "dons_investissements_net",
            "batiments",
            "agencements_amenagements_installations",
            "materiel_mobilier_actif_biologiques",
            "materiel_transport",
            "avances_acompte_immobilisations",
            "titres_participation",
            "autres_immobilisations_financieres",
            "actif_circulant_hao",
            "stock_encours",
            "fournisseurs_avances_versee",
            "clients",
            "autres_creances",
            "valeurs_mobilieres_placement",
            "disponibilites",
            "banque_cheque_postal_caisse_assimiles",
            "ecart_conversion_actif",
            "created_by",
            "updated_by",
        ]


class GetActifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = "__all__"


class EditActifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = [
            "id",
            "annee",
            "acheteur",
            "frais_developpement_prospection",
            "brevets_licences_logiciels",
            "droits_propriete_commerciale_baux",
            "autres_immo_incorporelles",
            "terrains",
            "dons_investissements_net",
            "batiments",
            "agencements_amenagements_installations",
            "materiel_mobilier_actif_biologiques",
            "materiel_transport",
            "avances_acompte_immobilisations",
            "titres_participation",
            "autres_immobilisations_financieres",
            "actif_circulant_hao",
            "stock_encours",
            "fournisseurs_avances_versee",
            "clients",
            "autres_creances",
            "valeurs_mobilieres_placement",
            "disponibilites",
            "banque_cheque_postal_caisse_assimiles",
            "ecart_conversion_actif",
            "created_by",
            "updated_by",
        ]


class PassifSysSCohadaSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = PassifS
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_capital(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddPassifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital",
            "capital_non_appele_apporteurs",
            "primes_liees_capital_social",
            "ecart_reevaluation",
            "reserves_indisponibles",
            "reserves_libres",
            "report_nouveau",
            "resultat_net_exercice",
            "subventions_investissements",
            "provisions_reglees",
            "emprunts_dettes_financieres_diverse",
            "dettes_location_vente",
            "provisions_risques_charges",
            "passif_circulant_hao",
            "clients_avances_recues",
            "fournisseurs_exploitation",
            "dettes_fiscales_sociales",
            "autres_dettes",
            "provisions_risques_court_terme",
            "banques_credit_escompte",
            "banques_etablissements_financiers_credit_caisse",
            "ecart_conversion_passif",
            "created_by",
            "updated_by",
        ]


class GetPassifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = "__all__"


class EditPassifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital",
            "capital_non_appele_apporteurs",
            "primes_liees_capital_social",
            "ecart_reevaluation",
            "reserves_indisponibles",
            "reserves_libres",
            "report_nouveau",
            "resultat_net_exercice",
            "subventions_investissements",
            "provisions_reglees",
            "emprunts_dettes_financieres_diverse",
            "dettes_location_vente",
            "provisions_risques_charges",
            "passif_circulant_hao",
            "clients_avances_recues",
            "fournisseurs_exploitation",
            "dettes_fiscales_sociales",
            "autres_dettes",
            "provisions_risques_court_terme",
            "banques_credit_escompte",
            "banques_etablissements_financiers_credit_caisse",
            "ecart_conversion_passif",
            "created_by",
            "updated_by",
        ]


class ResultatSysCohadaSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ResultatS
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_ventes_marchandises_a(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddResultatSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = [
            "id",
            "annee",
            "acheteur",
            "ventes_marchandises_a",
            "achats_marchandises",
            "variation_stock_marchandises",
            "ventes_produits_manufactures",
            "travaux_services_vendus_c",
            "produits_accessoires_d",
            "production_stockee",
            "production_immobilisee",
            "subvention_exploitation",
            "autres_produits",
            "transfert_charges_exploitation",
            "achats_matieres_premieres_fournitures_connexes",
            "variation_stock_matieres_premieres_fournitures_connexes",
            "autres_achats",
            "variation_stock_autres_fournitures",
            "transport",
            "services_exterieurs",
            "impots_taxes",
            "autres_depenses",
            "frais_personnel",
            "reprise_depreciations_amortissements_provision_pertes_valeurs_p",
            "reprise_depreciations_amortissements_provision_pertes_valeurs_m",
            "produits_financiers_assimiles",
            "reprise_provision_perte_valeur",
            "transfert_charges_financieres",
            "dotations_provisions_depreciations_financieres",
            "produits_cession_immobilisations",
            "autres_produits_hao",
            "valeur_comptable_cessions_actifs_immobilises",
            "autres_charges_hao",
            "participation_travailleurs",
            "charge_impot_revenu",
            "created_by",
            "updated_by",
        ]


class GetResultatSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = "__all__"


class EditResultatSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = [
            "id",
            "annee",
            "acheteur",
            "ventes_marchandises_a",
            "achats_marchandises",
            "variation_stock_marchandises",
            "ventes_produits_manufactures",
            "travaux_services_vendus_c",
            "produits_accessoires_d",
            "production_stockee",
            "production_immobilisee",
            "subvention_exploitation",
            "autres_produits",
            "transfert_charges_exploitation",
            "achats_matieres_premieres_fournitures_connexes",
            "variation_stock_matieres_premieres_fournitures_connexes",
            "autres_achats",
            "variation_stock_autres_fournitures",
            "transport",
            "services_exterieurs",
            "impots_taxes",
            "autres_depenses",
            "frais_personnel",
            "reprise_depreciations_amortissements_provision_pertes_valeurs_p",
            "reprise_depreciations_amortissements_provision_pertes_valeurs_m",
            "produits_financiers_assimiles",
            "reprise_provision_perte_valeur",
            "transfert_charges_financieres",
            "dotations_provisions_depreciations_financieres",
            "produits_cession_immobilisations",
            "autres_produits_hao",
            "valeur_comptable_cessions_actifs_immobilises",
            "autres_charges_hao",
            "participation_travailleurs",
            "charge_impot_revenu",
            "created_by",
            "updated_by",
        ]


class AssetsSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = Assets
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_banques_centrales(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = [
            "id",
            "annee",
            "acheteur",
            "caisse",
            "banques_centrales",
            "tresorerie_cpp",
            "autres_ets_credit",
            "a_terme",
            "credits_campagne",
            "credits_ordinaire",
            "credits_campagne_acc",
            "credits_ordinaire_acc",
            "creances_ordinaires",
            "affacturage",
            "titres_placement",
            "immobilisation_fin",
            "operation_credit_bail",
            "immobilisation_incorporelle",
            "immobilisation_corporelle",
            "actionnaire_ou_associe",
            "autres_actifs",
            "comptes_commande_divers",
            "created_by",
            "updated_by",
        ]


class GetAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = "__all__"


class EditAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = [
            "id",
            "annee",
            "acheteur",
            "caisse",
            "banques_centrales",
            "tresorerie_cpp",
            "autres_ets_credit",
            "a_terme",
            "credits_campagne",
            "credits_ordinaire",
            "credits_campagne_acc",
            "credits_ordinaire_acc",
            "creances_ordinaires",
            "affacturage",
            "titres_placement",
            "immobilisation_fin",
            "operation_credit_bail",
            "immobilisation_incorporelle",
            "immobilisation_corporelle",
            "actionnaire_ou_associe",
            "autres_actifs",
            "comptes_commande_divers",
            "created_by",
            "updated_by",
        ]


class LiabilitiesSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = Liabilities
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_tresorerie_ccp(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddLiabilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liabilities
        fields = [
            "id",
            "annee",
            "acheteur",
            "tresorerie_ccp",
            "autres_etablissement_credit",
            "a_terme",
            "comptes_epargne_court_terme",
            "comptes_epargne_terme",
            "bons_caisse",
            "autres_dette_a_vue",
            "autres_dette_a_terme",
            "titres_creance_autres_dettes",
            "compte_dordre_divers",
            "provision_pour_risque_charge",
            "provision_reglementee",
            "emprunt_subordonne_tire_emis",
            "subventions_investissement",
            "fonds_affecte",
            "fonds_pour_risque_bancaire_generaux",
            "capital_ou_dotation",
            "primes_liees_reserve_capital",
            "ecarts_reevaluation",
            "benefices_non_distribue",
            "resultat_net_exercie",
            "created_by",
            "updated_by",
        ]


class GetLiabilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liabilities
        fields = "__all__"


class EditLiabilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liabilities
        fields = [
            "id",
            "annee",
            "acheteur",
            "tresorerie_ccp",
            "autres_etablissement_credit",
            "a_terme",
            "comptes_epargne_court_terme",
            "comptes_epargne_terme",
            "bons_caisse",
            "autres_dette_a_vue",
            "autres_dette_a_terme",
            "titres_creance_autres_dettes",
            "compte_dordre_divers",
            "provision_pour_risque_charge",
            "provision_reglementee",
            "emprunt_subordonne_tire_emis",
            "subventions_investissement",
            "fonds_affecte",
            "fonds_pour_risque_bancaire_generaux",
            "capital_ou_dotation",
            "primes_liees_reserve_capital",
            "ecarts_reevaluation",
            "benefices_non_distribue",
            "resultat_net_exercie",
            "created_by",
            "updated_by",
        ]


class OffBalanceSheetSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = OffBalanceSheet
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_en_faveur_des_ets_credit(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddOffBalanceSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffBalanceSheet
        fields = [
            "id",
            "annee",
            "acheteur",
            "en_faveur_des_ets_credit",
            "en_faveur_clientele",
            "pour_compte_ets_credit",
            "pour_compte_clientele",
            "engagement_sur_titre",
            "recu_ets_credit",
            "recu_ets_credit2",
            "recu_clientele",
            "engagement_sur_titre2",
            "created_by",
            "updated_by",
        ]


class GetOffBalanceSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffBalanceSheet
        fields = "__all__"


class EditOffBalanceSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffBalanceSheet
        fields = [
            "id",
            "annee",
            "acheteur",
            "en_faveur_des_ets_credit",
            "en_faveur_clientele",
            "pour_compte_ets_credit",
            "pour_compte_clientele",
            "engagement_sur_titre",
            "recu_ets_credit",
            "recu_ets_credit2",
            "recu_clientele",
            "engagement_sur_titre2",
            "created_by",
            "updated_by",
        ]


class ExpensesSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = Expenses
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_interet_charges_assimilee_dette_interbancaire(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = [
            "id",
            "annee",
            "acheteur",
            "interet_charges_assimilee_dette_interbancaire",
            "interet_charge_assimilee_dette_clientele",
            "interet_charge_assimilee_titre_creance",
            "chargesc_compte_bloque_dactionnaire_emprunt_sub",
            "autres_interets_charges_assimilee",
            "charges_sur_op_credit_bail_assimile",
            "commissions",
            "charges_sur_titre_placement",
            "charges_sur_operation_change",
            "charges_sur_operation_hors_bilan",
            "frais_divers_exploitation_bancaire",
            "achat_marchandises",
            "stocks_vendus",
            "variations_stocks_marchanides",
            "frais_personnel",
            "autres_frais_generaux",
            "dotations_amortissement_provision_immobilisation",
            "solde_perte_creance_hors_bilan",
            "excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux",
            "charges_exceptionnelle",
            "pertes_exercice_anterieurs",
            "impot_sur_revenu",
            "total_charges",
            "created_by",
            "updated_by",
        ]


class GetExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = "__all__"


class EditExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = [
            "id",
            "annee",
            "acheteur",
            "interet_charges_assimilee_dette_interbancaire",
            "interet_charge_assimilee_dette_clientele",
            "interet_charge_assimilee_titre_creance",
            "chargesc_compte_bloque_dactionnaire_emprunt_sub",
            "autres_interets_charges_assimilee",
            "charges_sur_op_credit_bail_assimile",
            "commissions",
            "charges_sur_titre_placement",
            "charges_sur_operation_change",
            "charges_sur_operation_hors_bilan",
            "frais_divers_exploitation_bancaire",
            "achat_marchandises",
            "stocks_vendus",
            "variations_stocks_marchanides",
            "frais_personnel",
            "autres_frais_generaux",
            "dotations_amortissement_provision_immobilisation",
            "solde_perte_creance_hors_bilan",
            "excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux",
            "charges_exceptionnelle",
            "pertes_exercice_anterieurs",
            "impot_sur_revenu",
            "total_charges",
            "created_by",
            "updated_by",
        ]


class ProductsSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = Products
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_interets_produit_assimile_sur_pret_avance_interbancaire(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = [
            "id",
            "annee",
            "acheteur",
            "interets_produit_assimile_sur_pret_avance_interbancaire",
            "ineterets_produit_assimile_pret_avance_clientele",
            "interet_produit_sur_titre_dinvestissement",
            "revenu_gains_titre_pret_titre_subordonne",
            "autres_interets_produits_assimiles",
            "produits_leansing_operation_connexes",
            "commissions",
            "revenus_titre_negociable",
            "dividendes_produits_assimiles",
            "revenus_operation_de_change",
            "produits_opeations_hors_bilan",
            "produits_bancaire_divers",
            "marges_vente",
            "ventes_marchandises",
            "variation_stocks_marchandises",
            "produit_dexploitation_generale",
            "reprise_damortissement_provisions_sur_immobilisation",
            "solde_resultat_correction_valeur_sur_creance_hors_bilan",
            "excedent_reprise_fonds_pour_risque_bancaire_generaux",
            "produits_exceptionnels",
            "benefice_sur_exercice_anterieur",
            "perte",
            "created_by",
            "updated_by",
        ]


class GetProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = "__all__"


class EditProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = [
            "id",
            "annee",
            "acheteur",
            "interets_produit_assimile_sur_pret_avance_interbancaire",
            "ineterets_produit_assimile_pret_avance_clientele",
            "interet_produit_sur_titre_dinvestissement",
            "revenu_gains_titre_pret_titre_subordonne",
            "autres_interets_produits_assimiles",
            "produits_leansing_operation_connexes",
            "commissions",
            "revenus_titre_negociable",
            "dividendes_produits_assimiles",
            "revenus_operation_de_change",
            "produits_opeations_hors_bilan",
            "produits_bancaire_divers",
            "marges_vente",
            "ventes_marchandises",
            "variation_stocks_marchandises",
            "produit_dexploitation_generale",
            "reprise_damortissement_provisions_sur_immobilisation",
            "solde_resultat_correction_valeur_sur_creance_hors_bilan",
            "excedent_reprise_fonds_pour_risque_bancaire_generaux",
            "produits_exceptionnels",
            "benefice_sur_exercice_anterieur",
            "perte",
            "created_by",
            "updated_by",
        ]


class CommandesSerializer(serializers.ModelSerializer):
    client = CustomUserSerializer()
    acheteur = AcheteurSerializer()
    pays = PaysSerializer()
    ville = VilleSerializer()
    ref_type_rapport = ModeleRapportSerializer()
    devise_credit_demande = DeviseSerializer()
    devise_credit_recommande = DeviseSerializer()

    class Meta:
        model = Commande
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_credit_demande(self, value):
        return self.validate_decimal_field(value)

    def validate_credit_recommande(self, value):
        return self.validate_decimal_field(value)


class AddCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = [
            "id",
            "notre_ref",
            "reference_client",
            "date_recept_commande",
            "date_rapport",
            "delais",
            "priorite",
            "raison_sociale",
            "type_rapport",
            "ref_type_rapport",
            "credit_demande",
            "devise_credit_demande",
            "credit_recommande",
            "devise_credit_recommande",
            "numero_adresse",
            "rue_adresse",
            "code_postale_adresse",
            "telephone",
            "email",
            "ville",
            "client",
            "acheteur",
            "status",
        ]


class GetCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = "__all__"


class CheckCommandeSerializer(serializers.ModelSerializer):
    client = CustomUserSerializer()
    acheteur = AcheteurSerializer()
    ville = VilleSerializer()
    ref_type_rapport = ModeleRapportSerializer()
    devise_credit_demande = DeviseSerializer()
    devise_credit_recommande = DeviseSerializer()

    class Meta:
        model = Commande
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_credit_demande(self, value):
        return self.validate_decimal_field(value)

    def validate_credit_recommande(self, value):
        return self.validate_decimal_field(value)


class EditCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = [
            "id",
            "notre_ref",
            "reference_client",
            "date_recept_commande",
            "date_rapport",
            "delais",
            "priorite",
            "raison_sociale",
            "type_rapport",
            "ref_type_rapport",
            "credit_demande",
            "devise_credit_demande",
            "credit_recommande",
            "devise_credit_recommande",
            "numero_adresse",
            "rue_adresse",
            "code_postale_adresse",
            "telephone",
            "email",
            "ville",
            "client",
            "acheteur",
            "status",
        ]


class AlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = "__all__"


class AddAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = ["reference", "objet", "content"]


class EditAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = ["reference", "objet", "content"]


class DocumentAlerteSerializer(serializers.ModelSerializer):
    alerte = AlerteSerializer()

    class Meta:
        model = DocumentAlerte
        fields = "__all__"


class AddDocumentAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAlerte
        fields = ["titre", "fichier", "alerte"]


class EditDocumentAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAlerte
        fields = ["alerte", "titre", "fichier"]


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


class AddClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "nom",
            "email",
            "telephone",
            "adresse",
            "date_inscription",
            "actif",
        ]


class GetClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


class CheckClientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = "__all__"


class EditClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "nom",
            "email",
            "telephone",
            "adresse",
            "date_inscription",
            "actif",
        ]


class ContactSerializer(serializers.ModelSerializer):
    client = (
        ClientSerializer()
    )  # Utilisez le sérialiseur pour inclure les détails du pays

    class Meta:
        model = Contact
        fields = [
            "id",
            "client",
            "nom",
            "email",
            "telephone",
            "actif",
        ]


class AddContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "client",
            "nom",
            "email",
            "telephone",
            "actif",
        ]


class GetContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class CheckContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class EditContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "client",
            "nom",
            "email",
            "telephone",
            "actif",
        ]


class PortefeuilleSerializer(serializers.ModelSerializer):
    client = ClientSerializer()

    class Meta:
        model = Portefeuille
        fields = "__all__"


class AddPortefeuilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portefeuille
        fields = "__all__"


class AddPortefeuilleWithAcheteursSerializer(serializers.ModelSerializer):
    elements_surveillance_actifs = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ElementSurveillance.objects.all(), required=False
    )

    class Meta:
        model = Portefeuille
        fields = [
            "id",
            "client",
            "frequence_alertes",
            "nom",
            "elements_surveillance_actifs",
            "created_at",
            "updated_at",
        ]


class AddPortefeuilleWithAcheteursSerializer(serializers.ModelSerializer):
    acheteurs = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Portefeuille
        fields = ["client", "nom", "acheteurs"]

    def create(self, validated_data):
        acheteurs_data = validated_data.pop("acheteurs")
        portefeuille = Portefeuille.objects.create(**validated_data)

        for acheteur_id in acheteurs_data:
            PortefeuilleClient.objects.create(
                portefeuille=portefeuille, acheteur_id=acheteur_id
            )

        return portefeuille


class GetPortefeuilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portefeuille
        fields = "__all__"


class CheckPortefeuilleSerializer(serializers.ModelSerializer):
    client = ClientSerializer()  # Assurez-vous d'avoir un ClientSerializer défini

    class Meta:
        model = Portefeuille
        fields = "__all__"


class EditPortefeuilleSerializer(serializers.ModelSerializer):
    elements_surveillance_actifs = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ElementSurveillance.objects.all(), required=False
    )

    class Meta:
        model = Portefeuille
        fields = [
            "id",
            "client",
            "frequence_alertes",
            "nom",
            "elements_surveillance_actifs",
            "created_at",
            "updated_at",
        ]


class PortefeuilleClientSerializer(serializers.ModelSerializer):
    portefeuille = PortefeuilleSerializer()
    acheteur = AcheteurSerializer()  # Assurez-vous d'avoir un AcheteurSerializer défini

    class Meta:
        model = PortefeuilleClient
        fields = "__all__"


class AddPortefeuilleClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortefeuilleClient
        fields = ["id", "portefeuille", "acheteur", "categorie"]


class GetPortefeuilleClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortefeuilleClient
        fields = "__all__"


class CheckPortefeuilleClientSerializer(serializers.ModelSerializer):
    portefeuille = PortefeuilleSerializer()
    acheteur = AcheteurSerializer()  # Assurez-vous d'avoir un AcheteurSerializer défini

    class Meta:
        model = PortefeuilleClient
        fields = "__all__"


class CompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = "__all__"


class AddCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = ["id", "nom", "type_compte", "sous_type"]


class GetCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = "__all__"


class CheckCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = "__all__"


class EditCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = ["id", "nom", "type_compte", "sous_type"]


class ValeurCompteIrfsSerializer(serializers.ModelSerializer):

    compte = CompteFinancierIrfsSerializer()
    devise = DeviseSerializer()
    annee = AnneeSerializer()

    class Meta:
        model = ValeurCompteIrfs
        fields = "__all__"


class AddValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = ["id", "acheteur", "compte", "annee", "valeur", "devise"]


class GetValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = "__all__"


class CheckValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = "__all__"


class EditValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = ["id", "acheteur", "compte", "annee", "valeur", "devise"]


class RatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = "__all__"


class AddRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = ["id", "type_ratio", "nom", "formule"]


class GetRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = "__all__"


class CheckRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = "__all__"


class EditRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = ["id", "type_ratio", "nom", "formule"]


class ValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = "__all__"


class AddValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = ["id", "acheteur", "ratio", "annee", "valeur"]


class GetValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = "__all__"


class CheckValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = "__all__"


class EditValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = ["id", "acheteur", "ratio", "annee", "valeur"]





from django.contrib.auth import get_user_model
from rest_framework import serializers

CustomUser = get_user_model()


# serializers.py
class NewCustomUserSerializer(serializers.ModelSerializer):
    pays = serializers.SerializerMethodField()
    date_joined_formatted = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'telephone', 'activation', 'pays', 
            'date_joined', 'date_joined_formatted', 'avatar_url',
            'profession', 'address', 'email_cc'
        ]
    
    def get_pays(self, obj):
        if obj.pays:
            return {
                'id': obj.pays.id,
                'nom': obj.pays.nom,
                'code': obj.pays.code if hasattr(obj.pays, 'code') else None
            }
        return None
    
    def get_date_joined_formatted(self, obj):
        """Formate la date d'inscription"""
        if obj.date_joined:
            # Formater selon votre préférence
            # Option 1: "15/12/2024"
            # return obj.date_joined.strftime('%d/%m/%Y')
            
            # Option 2: "15 déc. 2024"
            mois_fr = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin',
                      'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
            return f"{obj.date_joined.day} {mois_fr[obj.date_joined.month-1]} {obj.date_joined.year}"
        
        return None
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

class GetCustomUserSerializerTwo(serializers.ModelSerializer):
    # pays = PaysSerializer()
    date_joined_formatted = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = "__all__"

    def get_date_joined_formatted(self, obj):
        # Formatez la date selon vos besoins
        return obj.date_joined.strftime("%d.%m.%Y à %H:%M:%S")


class AddCustomUserSerializerTwo(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "email_cc",
            "address",
            "activation",
            "telephone",
            "profession",
            "role",
            "pays",
        ]
        
        
class AddCustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    activation = serializers.BooleanField(default=True)
    pays = serializers.PrimaryKeyRelatedField(
        queryset=Pays.objects.all(),
        required=True,
        error_messages={
            'does_not_exist': 'Le pays sélectionné n\'existe pas.',
            'incorrect_type': 'Veuillez fournir un ID de pays valide.'
        }
    )
    
    class Meta:
        model = CustomUser
        fields = [
            "username", "first_name", "last_name", "email",
            "email_cc", "address", "activation", "telephone",
            "profession", "role", "pays", "password"
        ]
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'role': {'required': True},
            'pays': {'required': True},
        }
    
    def validate(self, data):
        # Validation de l'email
        if CustomUser.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({
                "email": "Cet email est déjà utilisé par un autre utilisateur."
            })
        
        # Validation du username
        if CustomUser.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError({
                "username": "Ce nom d'utilisateur est déjà pris."
            })
        
        # S'assurer que le pays existe
        if 'pays' in data and not Pays.objects.filter(id=data['pays'].id).exists():
            raise serializers.ValidationError({
                "pays": "Le pays sélectionné n'existe pas."
            })
        
        return data
    
    def create(self, validated_data):
        # Extraire le mot de passe
        password = validated_data.pop('password', None)
        
        # Créer l'utilisateur
        user = CustomUser(**validated_data)
        
        # Définir le mot de passe
        if password:
            user.set_password(password)
        else:
            # Générer un mot de passe par défaut
            import secrets
            default_password = secrets.token_urlsafe(12)
            user.set_password(default_password)
        
        user.save()
        return user



# serializers.py
class GetCustomUserSerializer(serializers.ModelSerializer):
    pays_id = serializers.IntegerField(source='pays.id', read_only=True)
    pays_nom = serializers.CharField(source='pays.nom', read_only=True)
    date_joined_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            "id", "username", "first_name", "last_name", "email",
            "email_cc", "address", "activation", "telephone", "profession",
            "role", "pays_id", "pays_nom", "date_joined", "date_joined_formatted"
        ]
    
    def get_date_joined_formatted(self, obj):
        if obj.date_joined:
            return obj.date_joined.strftime("%d.%m.%Y à %H:%M:%S")
        return None


class EditCustomUserSerializer(serializers.ModelSerializer):
    pays = serializers.PrimaryKeyRelatedField(
        queryset=Pays.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = CustomUser
        fields = [
            "username", "first_name", "last_name", "email",
            "email_cc", "address", "activation", "telephone",
            "profession", "role", "pays"
        ]
    
    def validate_email(self, value):
        # Exclure l'utilisateur actuel de la vérification d'unicité
        instance = self.instance
        if instance and CustomUser.objects.filter(email=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        elif not instance and CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def validate_username(self, value):
        instance = self.instance
        if instance and CustomUser.objects.filter(username=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        elif not instance and CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value


class EditCustomUserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "avatar"]







from rest_framework import serializers

from .models import ElementSurveillance


class ListElementSurveillanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementSurveillance
        fields = [
            "id",
            "nom",
            "code_interne",
            "categorie",
            "sous_categorie",
            "description",
        ]


class AddElementSurveillanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementSurveillance
        fields = ["nom", "code_interne", "categorie", "sous_categorie", "description"]


class DetailElementSurveillanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementSurveillance
        fields = [
            "id",
            "nom",
            "code_interne",
            "categorie",
            "sous_categorie",
            "description",
        ]


class EditElementSurveillanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementSurveillance
        fields = [
            "id",
            "nom",
            "code_interne",
            "categorie",
            "sous_categorie",
            "description",
        ]
        extra_kwargs = {
            "id": {"read_only": True},  # Le champ 'id' est en lecture seule
        }


class SearchElementSurveillanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementSurveillance
        fields = [
            "id",
            "nom",
            "code_interne",
            "categorie",
            "sous_categorie",
            "description",
        ]


from rest_framework import serializers

from .models import (Certification, ConformiteReglementation,
                     InnovationDeveloppement, StrategiePlanification)


class ListCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "id",
            "acheteur",
            "type_certification",
            "nom_certification",
            "date_obtention",
            "organisme_delivreur",
            "description",
        ]


class AddCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "acheteur",
            "type_certification",
            "nom_certification",
            "date_obtention",
            "organisme_delivreur",
            "description",
        ]


class DetailCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "id",
            "acheteur",
            "type_certification",
            "nom_certification",
            "date_obtention",
            "organisme_delivreur",
            "description",
        ]


class EditCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "id",
            "acheteur",
            "type_certification",
            "nom_certification",
            "date_obtention",
            "organisme_delivreur",
            "description",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class SearchCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "id",
            "acheteur",
            "type_certification",
            "nom_certification",
            "date_obtention",
            "organisme_delivreur",
            "description",
        ]





class ListInnovationDeveloppementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            "id",
            "acheteur",
            "type_innovation",
            "titre",
            "description",
            "date_debut",
            "date_fin",
        ]


class AddInnovationDeveloppementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            "acheteur",
            "type_innovation",
            "titre",
            "description",
            "date_debut",
            "date_fin",
        ]


class DetailInnovationDeveloppementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            "id",
            "acheteur",
            "type_innovation",
            "titre",
            "description",
            "date_debut",
            "date_fin",
        ]


class EditInnovationDeveloppementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            "id",
            "acheteur",
            "type_innovation",
            "titre",
            "description",
            "date_debut",
            "date_fin",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class SearchInnovationDeveloppementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            "id",
            "acheteur",
            "type_innovation",
            "titre",
            "description",
            "date_debut",
            "date_fin",
        ]


class ListStrategiePlanificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = [
            "id",
            "acheteur",
            "type_strategie",
            "description",
            "date_mise_en_place",
        ]


class AddStrategiePlanificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = ["acheteur", "type_strategie", "description", "date_mise_en_place"]


class DetailStrategiePlanificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = [
            "id",
            "acheteur",
            "type_strategie",
            "description",
            "date_mise_en_place",
        ]


class EditStrategiePlanificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = [
            "id",
            "acheteur",
            "type_strategie",
            "description",
            "date_mise_en_place",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class SearchStrategiePlanificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = [
            "id",
            "acheteur",
            "type_strategie",
            "description",
            "date_mise_en_place",
        ]


class ListConformiteReglementationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            "id",
            "acheteur",
            "type_conformite",
            "statut",
            "details_non_conformite",
            "date_verification",
            "organisme_controle",
            "commentaires",
        ]


class AddConformiteReglementationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            "acheteur",
            "type_conformite",
            "statut",
            "details_non_conformite",
            "date_verification",
            "organisme_controle",
            "commentaires",
        ]


class DetailConformiteReglementationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            "id",
            "acheteur",
            "type_conformite",
            "statut",
            "details_non_conformite",
            "date_verification",
            "organisme_controle",
            "commentaires",
        ]


class EditConformiteReglementationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            "id",
            "acheteur",
            "type_conformite",
            "statut",
            "details_non_conformite",
            "date_verification",
            "organisme_controle",
            "commentaires",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class SearchConformiteReglementationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            "id",
            "acheteur",
            "type_conformite",
            "statut",
            "details_non_conformite",
            "date_verification",
            "organisme_controle",
            "commentaires",
        ]


from rest_framework import serializers

from main.models import AlerteLog


class ListAlerteLogSerializer(serializers.ModelSerializer):
    portefeuille = PortefeuilleSerializer()
    acheteur = AcheteurSerializer()
    element_surveille = ListElementSurveillanceSerializer()

    class Meta:
        model = AlerteLog
        fields = [
            "id",
            "portefeuille",
            "acheteur",
            "element_surveille",
            "date_creation",
            "message",
            "lu",
        ]


class AddAlerteLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlerteLog
        fields = [
            "portefeuille",
            "acheteur",
            "element_surveille",
            "message",
            "content_type",
            "object_id",
        ]


class DetailAlerteLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlerteLog
        fields = [
            "id",
            "portefeuille",
            "acheteur",
            "element_surveille",
            "date_creation",
            "message",
            "lu",
            "content_type",
            "object_id",
        ]


class EditAlerteLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlerteLog
        fields = [
            "id",
            "portefeuille",
            "acheteur",
            "element_surveille",
            "message",
            "lu",
            "content_type",
            "object_id",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class SearchAlerteLogSerializer(serializers.ModelSerializer):
    portefeuille = PortefeuilleSerializer()
    acheteur = AcheteurSerializer()
    element_surveille = ListElementSurveillanceSerializer()

    class Meta:
        model = AlerteLog
        fields = [
            "id",
            "portefeuille",
            "acheteur",
            "element_surveille",
            "date_creation",
            "message",
            "lu",
            "content_type",
            "object_id",
        ]


class AssetsSerializer(serializers.ModelSerializer):
    """Serializer générique pour la lecture (liste et détail)."""

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    class Meta:
        model = Assets
        fields = "__all__"  # Affiche tous les champs du modèle


class AddAssetsSerializer(serializers.ModelSerializer):
    """Serializer pour l'ajout d'un nouvel actif."""

    class Meta:
        model = Assets
        # Exclut les champs auto-gérés
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        # Assigne l'utilisateur connecté à created_by
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class DetailAssetsSerializer(serializers.ModelSerializer):
    """Serializer pour l'ajout d'un nouvel actif."""

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    class Meta:
        model = Assets
        fields = "__all__"  # Affiche tous les champs du modèle


class EditAssetsSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un actif."""

    class Meta:
        model = Assets
        # Permet de modifier tous les champs sauf les IDs et les infos de création
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def update(self, instance, validated_data):
        # Assigne l'utilisateur connecté à updated_by
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class LiabilitiesSerializer(serializers.ModelSerializer):
    """
    Serializer générique pour la lecture des passifs (liste et détail).
    Affiche les détails des objets liés (Année, Acheteur, etc.).
    """

    # Relations avec d'autres modèles (en lecture seule)
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Propriétés calculées du modèle
    a_vue = serializers.ReadOnlyField()
    dette_interbancaire = serializers.ReadOnlyField()
    dette_envers_clientelle = serializers.ReadOnlyField()
    total_liabilities = serializers.ReadOnlyField()

    class Meta:
        model = Liabilities
        # Inclut tous les champs du modèle et les propriétés définies ci-dessus
        fields = "__all__"


# ---


class AddLiabilitiesSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'ajout (création) d'un nouvel enregistrement de passif.
    """

    class Meta:
        model = Liabilities
        # Exclut les champs qui sont gérés automatiquement par le système
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        """
        Personnalise la méthode de création pour assigner automatiquement
        l'utilisateur connecté au champ 'created_by'.
        """
        # Récupère l'utilisateur depuis le contexte de la requête
        user = self.context["request"].user
        validated_data["created_by"] = user

        # Crée l'objet Liabilities
        liabilities = Liabilities.objects.create(**validated_data)
        return liabilities

    def update(self, instance, validated_data):
        """
        Personnalise la méthode de mise à jour pour assigner automatiquement
        l'utilisateur connecté au champ 'updated_by'.
        """
        # Assigne l'utilisateur qui fait la mise à jour
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class ExpensesSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des Dépenses (liste et détail).

    Ce serializer inclut les détails des objets liés (Année, Acheteur, etc.)
    et expose les propriétés calculées du modèle comme des champs en lecture seule.
    """

    # Relations avec d'autres modèles (en lecture seule pour l'affichage)
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Propriétés calculées du modèle exposées en lecture seule
    interet_charges_assimilee = serializers.ReadOnlyField()
    charge_sur_operation_financiere = serializers.ReadOnlyField()
    prestation = serializers.ReadOnlyField()
    frais_generaux_dexploitation = serializers.ReadOnlyField()
    total_des_charges = serializers.ReadOnlyField()

    class Meta:
        model = Expenses
        # Inclut tous les champs du modèle ainsi que les propriétés définies ci-dessus
        fields = "__all__"


# ---


class AddExpensesSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'ajout et la modification d'un enregistrement de Dépense.
    """

    class Meta:
        model = Expenses
        # Exclut les champs gérés automatiquement par le système.
        # Le champ 'total_charges' est aussi exclu car il est calculé par la propriété.
        exclude = (
            "total_charges",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )

    def create(self, validated_data):
        """
        Personnalise la méthode de création pour assigner automatiquement
        l'utilisateur connecté au champ 'created_by'.
        """
        # Récupère l'utilisateur depuis le contexte de la requête
        user = self.context["request"].user
        validated_data["created_by"] = user

        # Crée l'objet Expenses
        expense = Expenses.objects.create(**validated_data)
        return expense

    def update(self, instance, validated_data):
        """
        Personnalise la méthode de mise à jour pour assigner automatiquement
        l'utilisateur connecté au champ 'updated_by'.
        """
        # Assigne l'utilisateur qui fait la mise à jour
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des Produits (Compte de Résultat).
    Expose les champs du modèle ainsi que les totaux calculés via les propriétés.
    """

    # Nested serializers pour afficher les détails des objets liés
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Exposition des propriétés du modèle comme des champs en lecture seule
    interet_produit_assimile = serializers.ReadOnlyField()
    revenu_d_operation_financiere = serializers.ReadOnlyField()
    autres_produits_exploitation = serializers.ReadOnlyField()
    total_produit = serializers.ReadOnlyField()

    class Meta:
        model = Products
        fields = "__all__"


# ---


class AddProductSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'ajout et la modification d'un enregistrement de Produit.
    """

    class Meta:
        model = Products
        # Exclut les champs qui sont automatiquement gérés par le système
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        """
        Assigne automatiquement l'utilisateur connecté lors de la création.
        """
        user = self.context["request"].user
        validated_data["created_by"] = user
        return Products.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Assigne automatiquement l'utilisateur connecté lors de la mise à jour.
        """
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class OffBalanceSheetSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des données du Hors Bilan.
    Expose les champs du modèle ainsi que les totaux calculés via les propriétés.
    """

    # Nested serializers pour afficher les détails des objets liés
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Exposition des propriétés du modèle comme des champs en lecture seule
    total_engagement_financement_donne = serializers.ReadOnlyField()
    total_engagement_garantie_donne = serializers.ReadOnlyField()
    total_engagements_donnes = serializers.ReadOnlyField()
    total_engagement_financement_recu = serializers.ReadOnlyField()
    total_engagements_recus = serializers.ReadOnlyField()

    class Meta:
        model = OffBalanceSheet
        fields = "__all__"  # Inclut tous les champs du modèle et ceux définis ci-dessus


class AddOffBalanceSheetSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et la mise à jour d'une instance OffBalanceSheet.
    N'inclut que les champs modifiables.
    """

    class Meta:
        model = OffBalanceSheet
        fields = [
            # Champs d'identification
            "type_bilan",
            "annee",
            "semestre",
            "acheteur",
            # Champs des engagements donnés
            "engagement_financement_donne_ets_credit",
            "engagement_financement_donne_clientele",
            "engagement_garantie_donne_ets_credit",
            "engagement_garantie_donne_clientele",
            "engagement_sur_titres_donnes",
            # Champs des engagements reçus
            "engagement_financement_recu_ets_credit",
            "engagement_financement_recu_clientele",
            "engagement_garantie_recu_ets_credit",
            "engagement_sur_titres_recus",
        ]

    def create(self, validated_data):
        # Logique pour associer l'utilisateur créateur, si nécessaire
        # Par exemple : validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Logique pour associer l'utilisateur modificateur, si nécessaire
        # Par exemple : validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


# Fichier: DANS VOTRE FICHIER serializers.py

from rest_framework import serializers

from .models import ActifIFRS, PassifIFRS, RatiosIFRS, ResultatIFRS

# Assurez-vous d'importer vos autres serializers (AnneeSerializer, etc.)
# from .serializers import AnneeSerializer, AcheteurSerializer, CustomUserSerializer


class ActifIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture (détail) d'un actif IFRS.
    Inclut les objets liés et le total calculé.
    """

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Propriété calculée du modèle
    total_actif_non_courant = serializers.ReadOnlyField()
    total_actif_courant = serializers.ReadOnlyField()
    total_actif = serializers.ReadOnlyField()

    class Meta:
        model = ActifIFRS
        fields = "__all__"


class AddActifIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'ajout et la modification d'un actif IFRS.
    """

    class Meta:
        model = ActifIFRS
        # Exclut les champs auto-gérés
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        # Assigne l'utilisateur qui effectue la création
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Assigne l'utilisateur qui effectue la mise à jour
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


# Fichier: DANS VOTRE FICHIER serializers.py


class PassifIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture d'un passif et capitaux propres IFRS.
    """

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Propriétés calculées
    total_capitaux_propres = serializers.ReadOnlyField()
    total_passif_non_courant = serializers.ReadOnlyField()
    total_passif_courant = serializers.ReadOnlyField()
    total_passif = serializers.ReadOnlyField()

    class Meta:
        model = PassifIFRS
        fields = "__all__"


class AddPassifIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et la modification d'un passif IFRS.
    """

    class Meta:
        model = PassifIFRS
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


# Fichier: DANS VOTRE FICHIER serializers.py


class ResultatIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture d'un compte de résultat IFRS.
    """

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Exposition des soldes intermédiaires de gestion
    # --- DÉBUT DE LA MODIFICATION ---
    # Déclaration des nouvelles propriétés de calcul
    chiffre_affaires = serializers.ReadOnlyField()
    autres_produits_operationnels = serializers.ReadOnlyField()
    total_produits = serializers.ReadOnlyField()
    cout_des_ventes = serializers.ReadOnlyField()
    charges_operationnelles = serializers.ReadOnlyField()
    amortissements_et_provisions = serializers.ReadOnlyField()
    total_charges = serializers.ReadOnlyField()
    resultat_operationnel = serializers.ReadOnlyField()
    resultat_financier = serializers.ReadOnlyField()
    resultat_avant_impot = serializers.ReadOnlyField()
    resultat_net = serializers.ReadOnlyField()
    # --- FIN DE LA MODIFICATION ---

    class Meta:
        model = ResultatIFRS
        fields = "__all__"


class AddResultatIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'ajout et la modification d'un compte de résultat IFRS.
    """

    class Meta:
        model = ResultatIFRS
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


# Fichier: serializers.py

# Fichier: serializers.py


class RatiosIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des ratios financiers.
    """

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)

    # Assurez-vous que TOUS ces ratios sont déclarés ici
    roa = serializers.ReadOnlyField()
    roe = serializers.ReadOnlyField()
    liquidite_generale = serializers.ReadOnlyField()
    liquidite_immediate = serializers.ReadOnlyField()
    ratio_endettement_total = serializers.ReadOnlyField()
    ratio_couverture_interets = serializers.ReadOnlyField()
    marge_brute = serializers.ReadOnlyField()
    marge_operationnelle = serializers.ReadOnlyField()
    marge_nette = serializers.ReadOnlyField()
    rotation_des_actifs = serializers.ReadOnlyField()
    dso = serializers.ReadOnlyField()

    class Meta:
        model = RatiosIFRS
        # La liste fields DOIT contenir les noms exacts des ratios
        fields = [
            "id",
            "annee",
            "acheteur",
            "roa",
            "roe",
            "liquidite_generale",  # <--- Ce champ doit être ici
            "liquidite_immediate",
            "ratio_endettement_total",  # <--- Et celui-ci aussi
            "ratio_couverture_interets",
            "marge_brute",
            "marge_operationnelle",
            "marge_nette",
            "rotation_des_actifs",
            "dso",
        ]



class TelephoneAcheteurSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = TelephoneAcheteur
        fields = "__all__"

class GetTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = "__all__"

class AddTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = [
            "telephone",
            "acheteur",
        ]

class EditTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = [
            "telephone",
        ]
 
 
 
        
        
class AdresseAcheteurSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = AdresseAcheteur
        fields = "__all__"

class GetAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = "__all__"

class AddAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = [
            "adresse",
            "acheteur",
        ]

class EditAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = [
            "adresse",
        ]
        
        
        
        
        
        
class PortableAcheteurSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = PortableAcheteur
        fields = "__all__"

class GetPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = "__all__"

class AddPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = [
            "portable",
            "acheteur",
        ]

class EditPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = [
            "portable",
        ]
        
        
        
        
        
class EmailAcheteurSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = EmailAcheteur
        fields = "__all__"

class GetEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = "__all__"

class AddEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = [
            "email",
            "acheteur",
        ]

class EditEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = [
            "email",
        ]
        
        
        
        
        
        
class DocumentSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = Document
        fields = "__all__"

class GetDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"

class AddDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "acheteur",
            "titre",
            "fichier",
            "description",
        ]

class EditDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "titre",
            "description",
            "fichier", # Le fichier est inclus car on pourrait vouloir le remplacer
        ]
        
        
        
        
        
class SwotSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = Swot
        fields = "__all__"

class GetSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = "__all__"

class AddSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = [
            "acheteur",
            "forces",
            "faiblesses",
            "opportunites",
            "menaces",
        ]

class EditSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = [
            "forces",
            "faiblesses",
            "opportunites",
            "menaces",
        ]
        
        
        
        
        
        
class ProduitServiceSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = ProduitService
        fields = "__all__"

class GetProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = "__all__"

class AddProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = [
            "acheteur",
            "produits",
            "services",
        ]

class EditProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = [
            "produits",
            "services",
        ]
        
        
        
        
        
class MarqueSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = Marque
        fields = "__all__"

class GetMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = "__all__"

class AddMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = [
            "acheteur",
            "marques",
        ]

class EditMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = [
            "marques",
        ]
        
        
        
        
        
class ProcedureCollectiveSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = ProcedureCollective
        fields = "__all__"

class GetProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = "__all__"

class AddProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = [
            "acheteur",
            "type_procedure",
            "date_ouverture",
            "date_cloture",
            "description",
        ]

class EditProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = [
            "type_procedure",
            "date_ouverture",
            "date_cloture",
            "description",
        ]
        
        
        
        
        
class RegistreCommerceSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = RegistreCommerce
        fields = "__all__"

class GetRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = "__all__"

class AddRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = [
            "acheteur",
            "numero",
            "date_inscription",
        ]

class EditRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = [
            "numero",
            "date_inscription",
        ]
        
        
        

class CotisationSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = Cotisation
        fields = "__all__"

class GetCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = "__all__"

class AddCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = [
            "acheteur",
            "numero",
            "date_affiliation",
        ]

class EditCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = [
            "numero",
            "date_affiliation",
        ]    
        

        
        
        
        
        
        
# serializers.py
from rest_framework import serializers
from .models import Marque

class ListMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ["id", "acheteur", "marques", "created_at", "updated_at"]

class AddMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ["acheteur", "marques"]

class DetailMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ["id", "acheteur", "marques", "created_at", "updated_at"]

class EditMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ["id", "acheteur", "marques", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ["id", "acheteur", "marques", "created_at", "updated_at"]










# serializers.py
from rest_framework import serializers
from .models import ProduitService

class ListProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ["id", "acheteur", "produits", "services", "created_at", "updated_at"]

class AddProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ["acheteur", "produits", "services"]

class DetailProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ["id", "acheteur", "produits", "services", "created_at", "updated_at"]

class EditProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ["id", "acheteur", "produits", "services", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ["id", "acheteur", "produits", "services", "created_at", "updated_at"]







# serializers.py
from rest_framework import serializers
from .models import Cotisation

class ListCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ["id", "acheteur", "numero", "date_affiliation", "created_at", "updated_at"]

class AddCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ["acheteur", "numero", "date_affiliation"]

class DetailCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ["id", "acheteur", "numero", "date_affiliation", "created_at", "updated_at"]

class EditCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ["id", "acheteur", "numero", "date_affiliation", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ["id", "acheteur", "numero", "date_affiliation", "created_at", "updated_at"]







# serializers.py
from rest_framework import serializers
from .models import Swot

class ListSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = ["id", "acheteur", "forces", "faiblesses", "opportunites", "menaces", "created_at", "updated_at"]

class AddSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = ["acheteur", "forces", "faiblesses", "opportunites", "menaces"]

class DetailSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = ["id", "acheteur", "forces", "faiblesses", "opportunites", "menaces", "created_at", "updated_at"]

class EditSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = ["id", "acheteur", "forces", "faiblesses", "opportunites", "menaces", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}





# serializers.py
from rest_framework import serializers
from .models import RegistreCommerce

class ListRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = ["id", "acheteur", "numero", "date_inscription", "created_at", "updated_at"]

class AddRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = ["acheteur", "numero", "date_inscription"]

class DetailRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = ["id", "acheteur", "numero", "date_inscription", "created_at", "updated_at"]

class EditRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = ["id", "acheteur", "numero", "date_inscription", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}









# serializers.py
from rest_framework import serializers
from .models import ProcedureCollective

class ListProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = ["id", "acheteur", "type_procedure", "date_ouverture", "date_cloture", "description", "created_at", "updated_at"]

class AddProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = ["acheteur", "type_procedure", "date_ouverture", "date_cloture", "description"]

class DetailProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = ["id", "acheteur", "type_procedure", "date_ouverture", "date_cloture", "description", "created_at", "updated_at"]

class EditProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = ["id", "acheteur", "type_procedure", "date_ouverture", "date_cloture", "description", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}










# serializers.py
from rest_framework import serializers
from .models import Document

class ListDocumentSerializer(serializers.ModelSerializer):
    fichier_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "acheteur", "titre", "fichier", "fichier_url", "description", "created_at", "updated_at"]

    def get_fichier_url(self, obj):
        if obj.fichier:
            return obj.fichier.url
        return None

class AddDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["acheteur", "titre", "fichier", "description"]

class DetailDocumentSerializer(serializers.ModelSerializer):
    fichier_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "acheteur", "titre", "fichier", "fichier_url", "description", "created_at", "updated_at"]

    def get_fichier_url(self, obj):
        if obj.fichier:
            return obj.fichier.url
        return None

class EditDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "acheteur", "titre", "fichier", "description", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}









class ListAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = ["id", "adresse", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class AddAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = ["adresse", "acheteur"]

class DetailAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = ["id", "adresse", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class EditAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = ["id", "adresse", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "created_by": {"read_only": True},
            "acheteur": {"read_only": True}
        }












class ListPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["id", "portable", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class AddPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["portable", "acheteur"]

class DetailPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["id", "portable", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class EditPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["id", "portable", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "created_by": {"read_only": True},
            "acheteur": {"read_only": True}
        }










class ListTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = ["id", "telephone", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class AddTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = ["telephone", "acheteur"]

class DetailTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = ["id", "telephone", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class EditTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = ["id", "telephone", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "created_by": {"read_only": True},
            "acheteur": {"read_only": True}
        }










class ListEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = ["id", "email", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class AddEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = ["email", "acheteur"]

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Veuillez entrer une adresse email valide.")
        return value

class DetailEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = ["id", "email", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class EditEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = ["id", "email", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "created_by": {"read_only": True},
            "acheteur": {"read_only": True}
        }

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Veuillez entrer une adresse email valide.")
        return value









class CategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "poids", "active"]

class SubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    category = CategoryNaceCodeSerializer(read_only=True)

    class Meta:
        model = SubCategoryNaceCode
        fields = ["id", "code", "libelle", "poids", "active", "category"]



class ListCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    code = SubCategoryNaceCodeSerializer(read_only=True)

    class Meta:
        model = CodeNaceAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]

class AddCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNaceAcheteur
        fields = ["acheteur", "code"]

class DetailCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    code = SubCategoryNaceCodeSerializer(read_only=True)

    class Meta:
        model = CodeNaceAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]

class EditCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNaceAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "acheteur": {"read_only": True}
        }






class CategoryNafCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNafCode
        fields = ["id", "code", "libelle", "active"]

class SubCategoryNafCodeSerializer(serializers.ModelSerializer):
    category = CategoryNafCodeSerializer(read_only=True)

    class Meta:
        model = SubCategoryNafCode
        fields = ["id", "code", "libelle", "active", "category"]

class ListCodeNafAcheteurSerializer(serializers.ModelSerializer):
    code = SubCategoryNafCodeSerializer(read_only=True)

    class Meta:
        model = CodeNafAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]

class AddCodeNafAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNafAcheteur
        fields = ["acheteur", "code"]

class DetailCodeNafAcheteurSerializer(serializers.ModelSerializer):
    code = SubCategoryNafCodeSerializer(read_only=True)

    class Meta:
        model = CodeNafAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]

class EditCodeNafAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNafAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "acheteur": {"read_only": True}
        }






class CommandeSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(source='client.username', read_only=True)
    pays_nom = serializers.CharField(source='pays.nom', read_only=True)
    validateur_username = serializers.CharField(source='validateur.username', read_only=True)
    
    class Meta:
        model = Commande
        # Add the new fields here
        fields = [
            'id', 'notre_ref', 'reference_client', 'type_rapport', 'raison_sociale', 
            'date_recept_commande', 'date_rapport', 'priorite', 'status',
            'client', 'client_username', 'pays', 'pays_nom', 'validateur',
            'validateur_username', 'date_envoi_client', 'email_envoye',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['validateur', 'date_envoi_client', 'email_envoye']

class AffectationAnalysteSerializer(serializers.ModelSerializer):
    analyste = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = AffectationAnalyste
        fields = ['id', 'commande', 'analyste', 'date_affectation']

class ValidationRapportSerializer(serializers.ModelSerializer):
    validateur = CustomUserSerializer(read_only=True)

    class Meta:
        model = ValidationRapport
        fields = ['id', 'rapport', 'validateur', 'status', 'commentaire', 'date_validation']

class RapportSerializer(serializers.ModelSerializer):
    analyste = CustomUserSerializer(read_only=True)
    validation = ValidationRapportSerializer(source='validationrapport', read_only=True)
    
    class Meta:
        model = Rapport
        fields = ['id', 'commande', 'analyste', 'fichier', 'date_soumission', 'validation']

class SuiviCommandeSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = SuiviCommande
        fields = ['id', 'commande', 'user', 'action', 'type', 'commentaire', 'date_action']

class NotificationSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'type', 'message', 'is_read', 'created_at']
        
        
        
        
        
        
        
        
        
        
        
        
# --- Sérialiseurs pour le modèle ActifC ---
class ActifClassiqueSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Inclusion des propriétés de calcul en lecture seule
    elements_incorporels = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    elements_corporels = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    elements_financiers = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_I = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    stocks = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    creances = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    disponibilites_vmp = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_II = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    compte_regul = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_III = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    general_total = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ActifC
        fields = '__all__'


class AddActifClassiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifC
        fields = [
            'annee', 'acheteur', 'capital_souscrit_non_app', 'frais_recherche_developpement',
            'brevet_licence_logiciels', 'fonds_commercial', 'autres_immobilisations_incorporelles',
            'terrains', 'constructions', 'materiels_et_outils', 'materiel_de_transport',
            'autres_immos_corp', 'immos_en_cours', 'avances_et_acptes',
            'participations', 'prets', 'autres', 'stocks_mp', 'stocks_encours_mp',
            'stocks_pf', 'stocks_encours_pf', 'stocks_encours_services', 'stocks_mses',
            'avances_acptes_verses', 'clients_et_cptes_rattaches', 'autres_creances',
            'valeurs_a_encaisser', 'banques_cheques_postaux_caisse', 'cca',
            'charges_a_repartir_et_frais_etablissement', 'primes_de_rbt', 'eca', 'eene',
            'amortissements', 'provisions_stocks', 'provisions_creances', 'provisions_vmp',
            'effectif' # J'ajoute l'effectif car il semble être une donnée d'entrée
        ]

class EditActifClassiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifC
        fields = [
            'annee', 'acheteur', 'capital_souscrit_non_app', 'frais_recherche_developpement',
            'brevet_licence_logiciels', 'fonds_commercial', 'autres_immobilisations_incorporelles',
            'terrains', 'constructions', 'materiels_et_outils', 'materiel_de_transport',
            'autres_immos_corp', 'immos_en_cours', 'avances_et_acptes',
            'participations', 'prets', 'autres', 'stocks_mp', 'stocks_encours_mp',
            'stocks_pf', 'stocks_encours_pf', 'stocks_encours_services', 'stocks_mses',
            'avances_acptes_verses', 'clients_et_cptes_rattaches', 'autres_creances',
            'valeurs_a_encaisser', 'banques_cheques_postaux_caisse', 'cca',
            'charges_a_repartir_et_frais_etablissement', 'primes_de_rbt', 'eca', 'eene',
            'amortissements', 'provisions_stocks', 'provisions_creances', 'provisions_vmp',
            'effectif'
        ]

# --- Sérialiseurs pour le modèle PassifC ---
class PassifClassiqueSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Inclusion des propriétés de calcul
    total_I = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_II = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_III = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_IV = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_general = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = PassifC
        fields = '__all__'


class AddPassifClassiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifC
        fields = [
            'annee', 'acheteur', 'capital_social', 'primes', 'ecarts_de_reevaluation',
            'reserve', 'report_a_nouveau', 'resultat_exercice', 'subv_invest',
            'provision_regl', 'emprunts', 'dette_credit_bail_contrat_assimile',
            'dettes_financiere_diverses', 'provision_financiere_risque_charge',
            'dettes_fournisseurs_divers', 'avance_et_acomptes_recu', 'dettes',
            'dettes_fiscales_sociales', 'autres_dettes', 'banques_credit_escompte',
            'banque_credit_caisse', 'banques_decouvert', 'ecart_conversion_passif',
        ]


class EditPassifClassiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifC
        fields = [
            'annee', 'acheteur', 'capital_social', 'primes', 'ecarts_de_reevaluation',
            'reserve', 'report_a_nouveau', 'resultat_exercice', 'subv_invest',
            'provision_regl', 'emprunts', 'dette_credit_bail_contrat_assimile',
            'dettes_financiere_diverses', 'provision_financiere_risque_charge',
            'dettes_fournisseurs_divers', 'avance_et_acomptes_recu', 'dettes',
            'dettes_fiscales_sociales', 'autres_dettes', 'banques_credit_escompte',
            'banque_credit_caisse', 'banques_decouvert', 'ecart_conversion_passif',
        ]

# --- Sérialiseurs pour le modèle ResultatC ---
class ResultatClassiqueSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Inclusion des propriétés de calcul
    ca = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_I = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    marge_brute = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    valeur_ajoutee = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    excedent_brut_ex = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    financier_total_I = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    financier_total_II = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_financier = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_courant_avant_impots = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    excep_total_I = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    excep_total_II = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_excep = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_exercice = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ResultatC
        fields = '__all__'


class AddResultatClassiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatC
        fields = [
            'annee', 'acheteur', 'vente_de_mdses', 'ventes_de_produits_fabriques',
            'travaux_services_vendus', 'produit_accessoires', 'production_imblise',
            'subventions_exploitations', 'production_stockee', 'reprises_de_provision',
            'transferts_charges', 'autres_produits', 'achat_mdses', 'variation_stock_mdses',
            'achat_mp_autres_appro', 'var_stk_mp_app', 'autres_achats',
            'variation_de_stocks_autres_appro', 'transports', 'services_ext',
            'impots_taxes', 'autres_charges_valeur_ajoutee', 'charges_personnel',
            'dotation_aux_amorts', 'dotation_aux_provisions',
            'autres_charges_excedent_brute', 'revenus_fin_assimiles',
            'prof_vmp_et_cre_actif_immo', 'interets_produit_assim',
            'reprise_prov_et_transfert', 'diff_positive_de_change',
            'prod_nets_cessions_vmp', 'dap', 'frais_fin_charges_assi',
            'diff_negatives_de_change', 'ch_nettes_cessions_vmp',
            'sur_op_gestion_prod_except', 'sur_op_en_capital_prod_except',
            'reprise_prov_transfert', 'sur_op_gestion_charg_except',
            'sur_op_en_capital_charg_except', 'dap_et_transfert_charg_except',
            'participation_salairies', 'impot_sur_benefices',
        ]


class EditResultatClassiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatC
        fields = [
            'annee', 'acheteur', 'vente_de_mdses', 'ventes_de_produits_fabriques',
            'travaux_services_vendus', 'produit_accessoires', 'production_imblise',
            'subventions_exploitations', 'production_stockee', 'reprises_de_provision',
            'transferts_charges', 'autres_produits', 'achat_mdses', 'variation_stock_mdses',
            'achat_mp_autres_appro', 'var_stk_mp_app', 'autres_achats',
            'variation_de_stocks_autres_appro', 'transports', 'services_ext',
            'impots_taxes', 'autres_charges_valeur_ajoutee', 'charges_personnel',
            'dotation_aux_amorts', 'dotation_aux_provisions',
            'autres_charges_excedent_brute', 'revenus_fin_assimiles',
            'prof_vmp_et_cre_actif_immo', 'interets_produit_assim',
            'reprise_prov_et_transfert', 'diff_positive_de_change',
            'prod_nets_cessions_vmp', 'dap', 'frais_fin_charges_assi',
            'diff_negatives_de_change', 'ch_nettes_cessions_vmp',
            'sur_op_gestion_prod_except', 'sur_op_en_capital_prod_except',
            'reprise_prov_transfert', 'sur_op_gestion_charg_except',
            'sur_op_en_capital_charg_except', 'dap_et_transfert_charg_except',
            'participation_salairies', 'impot_sur_benefices',
        ]
        
        
        
        
        
        
        
        
        
        
        
        


# --- Sérialiseurs pour le modèle ActifS ---
class ActifSysOhadaSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Inclusion des propriétés de calcul en lecture seule
    immobilisations_incorporelles = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    immobilisations_corporelles = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    immobilisations_financieres = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif_immobilise = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    creances_emplois_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_tresorerie_equivalents = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif_circulant = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ActifS
        fields = '__all__'


class AddActifSysOhadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = [
            'annee', 'acheteur', 'frais_developpement_prospection', 'brevets_licences_logiciels',
            'droits_propriete_commerciale_baux', 'autres_immo_incorporelles', 'terrains',
            'dons_investissements_net', 'batiments', 'agencements_amenagements_installations',
            'materiel_mobilier_actif_biologiques', 'materiel_transport',
            'avances_acompte_immobilisations', 'titres_participation',
            'autres_immobilisations_financieres', 'actif_circulant_hao', 'stock_encours',
            'fournisseurs_avances_versee', 'clients', 'autres_creances',
            'valeurs_mobilieres_placement', 'disponibilites',
            'banque_cheque_postal_caisse_assimiles', 'ecart_conversion_actif'
        ]


class EditActifSysOhadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = [
            'annee', 'acheteur', 'frais_developpement_prospection', 'brevets_licences_logiciels',
            'droits_propriete_commerciale_baux', 'autres_immo_incorporelles', 'terrains',
            'dons_investissements_net', 'batiments', 'agencements_amenagements_installations',
            'materiel_mobilier_actif_biologiques', 'materiel_transport',
            'avances_acompte_immobilisations', 'titres_participation',
            'autres_immobilisations_financieres', 'actif_circulant_hao', 'stock_encours',
            'fournisseurs_avances_versee', 'clients', 'autres_creances',
            'valeurs_mobilieres_placement', 'disponibilites',
            'banque_cheque_postal_caisse_assimiles', 'ecart_conversion_actif'
        ]



# --- Sérialiseurs pour le modèle PassifS ---
class PassifSysOhadaSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Inclusion des propriétés de calcul
    total_capitaux_propres_ressources_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_dettes_financieres_ressources_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_ressources_stables = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passifs_courants = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_tresorerie_equivalents = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passifs = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = PassifS
        fields = '__all__'


class AddPassifSysOhadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = [
            'annee', 'acheteur', 'capital', 'capital_non_appele_apporteurs',
            'primes_liees_capital_social', 'ecart_reevaluation', 'reserves_indisponibles',
            'reserves_libres', 'report_nouveau', 'resultat_net_exercice',
            'subventions_investissements', 'provisions_reglees',
            'emprunts_dettes_financieres_diverse', 'dettes_location_vente',
            'provisions_risques_charges', 'passif_circulant_hao',
            'clients_avances_recues', 'fournisseurs_exploitation',
            'dettes_fiscales_sociales', 'autres_dettes',
            'provisions_risques_court_terme', 'banques_credit_escompte',
            'banques_etablissements_financiers_credit_caisse',
            'ecart_conversion_passif'
        ]


class EditPassifSysOhadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = [
            'annee', 'acheteur', 'capital', 'capital_non_appele_apporteurs',
            'primes_liees_capital_social', 'ecart_reevaluation', 'reserves_indisponibles',
            'reserves_libres', 'report_nouveau', 'resultat_net_exercice',
            'subventions_investissements', 'provisions_reglees',
            'emprunts_dettes_financieres_diverse', 'dettes_location_vente',
            'provisions_risques_charges', 'passif_circulant_hao',
            'clients_avances_recues', 'fournisseurs_exploitation',
            'dettes_fiscales_sociales', 'autres_dettes',
            'provisions_risques_court_terme', 'banques_credit_escompte',
            'banques_etablissements_financiers_credit_caisse',
            'ecart_conversion_passif'
        ]



# --- Sérialiseurs pour le modèle ResultatS ---
class ResultatSysOhadaSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Inclusion des propriétés de calcul
    marge_commerciale = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    chiffre_affaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    valeur_ajoutee = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    excedent_brute_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_financier = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_activites_ordinaires_xe = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_activites_ordinaires_tn = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_net = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ResultatS
        fields = '__all__'


class AddResultatSysOhadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = [
            'annee', 'acheteur', 'ventes_marchandises_a', 'achats_marchandises',
            'variation_stock_marchandises', 'ventes_produits_manufactures',
            'travaux_services_vendus_c', 'produits_accessoires_d',
            'production_stockee', 'production_immobilisee', 'subvention_exploitation',
            'autres_produits', 'transfert_charges_exploitation',
            'achats_matieres_premieres_fournitures_connexes',
            'variation_stock_matieres_premieres_fournitures_connexes',
            'autres_achats', 'variation_stock_autres_fournitures',
            'transport', 'services_exterieurs', 'impots_taxes', 'autres_depenses',
            'frais_personnel',
            'reprise_depreciations_amortissements_provision_pertes_valeurs_p',
            'reprise_depreciations_amortissements_provision_pertes_valeurs_m',
            'produits_financiers_assimiles', 'reprise_provision_perte_valeur',
            'transfert_charges_financieres', 'charges_financieres_assimilees',
            'dotations_provisions_depreciations_financieres',
            'produits_cession_immobilisations', 'autres_produits_hao',
            'valeur_comptable_cessions_actifs_immobilises', 'autres_charges_hao',
            'participation_travailleurs', 'charge_impot_revenu',
        ]


class EditResultatSysOhadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = [
            'annee', 'acheteur', 'ventes_marchandises_a', 'achats_marchandises',
            'variation_stock_marchandises', 'ventes_produits_manufactures',
            'travaux_services_vendus_c', 'produits_accessoires_d',
            'production_stockee', 'production_immobilisee', 'subvention_exploitation',
            'autres_produits', 'transfert_charges_exploitation',
            'achats_matieres_premieres_fournitures_connexes',
            'variation_stock_matieres_premieres_fournitures_connexes',
            'autres_achats', 'variation_stock_autres_fournitures',
            'transport', 'services_exterieurs', 'impots_taxes', 'autres_depenses',
            'frais_personnel',
            'reprise_depreciations_amortissements_provision_pertes_valeurs_p',
            'reprise_depreciations_amortissements_provision_pertes_valeurs_m',
            'produits_financiers_assimiles', 'reprise_provision_perte_valeur',
            'transfert_charges_financieres', 'charges_financieres_assimilees',
            'dotations_provisions_depreciations_financieres',
            'produits_cession_immobilisations', 'autres_produits_hao',
            'valeur_comptable_cessions_actifs_immobilises', 'autres_charges_hao',
            'participation_travailleurs', 'charge_impot_revenu',
        ]
        
        
        
        
        
        
        
        
        
        
        
        
        


# --- Sérialiseurs pour le modèle ActifA ---
class ActifAnglaisSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Inclusion des propriétés de calcul en lecture seule
    total_actifs_non_courants = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actifs_courants = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ActifA
        fields = '__all__'


class AddActifAnglaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifA
        fields = [
            'annee', 'acheteur', 'biens_installations_equipements', 'inventaire',
            'creances_commerciales_autres_creances', 'actif_impots_courant', 'caisses_banques'
        ]


class EditActifAnglaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifA
        fields = [
            'annee', 'acheteur', 'biens_installations_equipements', 'inventaire',
            'creances_commerciales_autres_creances', 'actif_impots_courant', 'caisses_banques'
        ]


# --- Sérialiseurs pour le modèle PassifA ---
class PassifAnglaisSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Inclusion des propriétés de calcul
    total_fonds_propres = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passifs_non_courants = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passifs_courants = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passif = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = PassifA
        fields = '__all__'


class AddPassifAnglaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifA
        fields = [
            'annee', 'acheteur', 'capital_reserves', 'capital_declare',
            'benefices_non_distribues', 'pret_bancaire',
            'compte_courant_administrateurs', 'dettes_commerciales_autres_dettes',
            'decouvert_bancaire', 'impots'
        ]


class EditPassifAnglaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifA
        fields = [
            'annee', 'acheteur', 'capital_reserves', 'capital_declare',
            'benefices_non_distribues', 'pret_bancaire',
            'compte_courant_administrateurs', 'dettes_commerciales_autres_dettes',
            'decouvert_bancaire', 'impots'
        ]


# --- Sérialiseurs pour le modèle ResultatA ---
class ResultatAnglaisSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)

    # Inclusion des propriétés de calcul
    marge_brute = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_avant_interets_impots = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_avant_impots = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_net = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    benefices_non_distribues = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ResultatA
        fields = '__all__'


class AddResultatAnglaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatA
        fields = [
            'annee', 'acheteur', 'produits_activites_ordinaires', 'ventes',
            'charges_exploitation', 'frais_vente_generaux_administratifs',
            'autres_revenus', 'frais_financier', 'charge_impot_sur_revenu',
            'autres_elements_resultat_global'
        ]


class EditResultatAnglaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatA
        fields = [
            'annee', 'acheteur', 'produits_activites_ordinaires', 'ventes',
            'charges_exploitation', 'frais_vente_generaux_administratifs',
            'autres_revenus', 'frais_financier', 'charge_impot_sur_revenu',
            'autres_elements_resultat_global'
        ]
        
        
        
        
# main/serializers.py
from rest_framework import serializers
from .models import (
    ScoringSansBilanAcheteur,
    FormeJuridique,
    ModeleComportementPaiement,
    ModeleAgeSociete,
    ModeleAvisCommercial,
    ModeleBail,
    CategoryNaceCode,
)

# serializers.py
class ModeleComportementPaiementScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementPaiement
        fields = ["id", "code", "libelle", "poids"]

class FormeJuridiqueScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormeJuridique
        fields = ["id", "code", "libelle", "poids"]

class ModeleAgeSocieteScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAgeSociete
        fields = ["id", "code", "libelle", "poids"]

class ModeleAvisCommercialScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAvisCommercial
        fields = ["id", "code", "libelle", "poids"]

class ModeleBailScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleBail
        fields = ["id", "code", "libelle", "poids"]

class CategoryNaceCodeScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "poids"]
    
    
    
class ScoringSansBilanAcheteurSerializer(serializers.ModelSerializer):
    # Champs en lecture seule pour l'affichage
    categories_nace_ref = CategoryNaceCodeScoringSerializer(many=True, read_only=True)
    comportement_de_paiement_ref = ModeleComportementPaiementScoringSerializer(read_only=True)
    age_company_ref = ModeleAgeSocieteScoringSerializer(read_only=True)
    forme_juridique = FormeJuridiqueScoringSerializer(read_only=True)
    avis_commercial_ref = ModeleAvisCommercialScoringSerializer(read_only=True)
    locaux_ref = ModeleBailScoringSerializer(read_only=True)
    
    # Champs en écriture pour la mise à jour
    comportement_de_paiement_ref_id = serializers.PrimaryKeyRelatedField(
        queryset=ModeleComportementPaiement.objects.all(), 
        source='comportement_de_paiement_ref', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    age_company_ref_id = serializers.PrimaryKeyRelatedField(
        queryset=ModeleAgeSociete.objects.all(), 
        source='age_company_ref', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    forme_juridique_id = serializers.PrimaryKeyRelatedField(
        queryset=FormeJuridique.objects.all(), 
        source='forme_juridique', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    avis_commercial_ref_id = serializers.PrimaryKeyRelatedField(
        queryset=ModeleAvisCommercial.objects.all(), 
        source='avis_commercial_ref', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    locaux_ref_id = serializers.PrimaryKeyRelatedField(
        queryset=ModeleBail.objects.all(), 
        source='locaux_ref', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    categories_nace_ref_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ScoringSansBilanAcheteur
        fields = [
            "id", "code", "acheteur", 
            "comportement_de_paiement_ref", "comportement_de_paiement_ref_id",
            "age_company_ref", "age_company_ref_id",
            "forme_juridique", "forme_juridique_id", 
            "avis_commercial_ref", "avis_commercial_ref_id",
            "locaux_ref", "locaux_ref_id",
            "categories_nace_ref", "categories_nace_ref_ids",
            "scoring_value", "interpretation", "commentaire", 
            "created_at", "updated_at"
        ]
        read_only_fields = ["scoring_value", "interpretation", "created_at", "updated_at"]
        
    def get_object(self):
        acheteur_id = self.kwargs.get("acheteur_id")
        return get_object_or_404(ScoringSansBilanAcheteur, acheteur_id=acheteur_id)

    def update(self, instance, validated_data):
        print("🔄 Mise à jour du scoring...")
        
        # Extraire les données pour les relations ManyToMany
        categories_nace_ids = validated_data.pop('categories_nace_ref_ids', None)
        
        # Mettre à jour les champs simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Sauvegarder d'abord pour avoir un ID
        instance.save()
        
        # Mettre à jour les catégories NACE
        if categories_nace_ids is not None:
            instance.categories_nace_ref.set(categories_nace_ids)
            print(f"📝 Catégories NACE mises à jour: {categories_nace_ids}")
        
        # Sauvegarder à nouveau pour recalculer le score
        instance.save()
        
        print(f"🎯 Score final: {instance.scoring_value}")
        return instance





from rest_framework import serializers
from django.db import models
from decimal import Decimal

class ScoreACREMACBilanSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField(required=True)
    annee_n = serializers.IntegerField(required=True)
    annee_n1 = serializers.IntegerField(required=True)
    annee_n2 = serializers.IntegerField(required=True)
    
    # Données calculées (en lecture seule)
    score_n = serializers.FloatField(read_only=True)
    score_n1 = serializers.FloatField(read_only=True)
    score_n2 = serializers.FloatField(read_only=True)
    probabilite_defaillance = serializers.FloatField(read_only=True)
    classe_risque = serializers.CharField(read_only=True)
    commentaire = serializers.CharField(read_only=True)
    
    # Ratios pour l'année N
    r1_ff_ebe = serializers.FloatField(read_only=True)
    r2_creances_dettes_ct = serializers.FloatField(read_only=True)
    r3_capitaux_permanents_passif = serializers.FloatField(read_only=True)
    r4_va_ca = serializers.FloatField(read_only=True)
    r5_tresorerie_ventes_j = serializers.FloatField(read_only=True)
    r6_fdr_ca_j = serializers.FloatField(read_only=True)

class CalculScoreACREMACBilanSerializer(serializers.Serializer):
    # Données d'entrée pour le calcul
    frais_financiers = serializers.DecimalField(max_digits=15, decimal_places=2)
    ebe = serializers.DecimalField(max_digits=15, decimal_places=2)
    creances_disponibilites = serializers.DecimalField(max_digits=15, decimal_places=2)
    dettes_court_terme = serializers.DecimalField(max_digits=15, decimal_places=2)
    capitaux_permanents = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_passif = serializers.DecimalField(max_digits=15, decimal_places=2)
    valeur_ajoutee = serializers.DecimalField(max_digits=15, decimal_places=2)
    chiffre_affaires = serializers.DecimalField(max_digits=15, decimal_places=2)
    tresorerie = serializers.DecimalField(max_digits=15, decimal_places=2)
    fonds_roulement = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Coefficients fixes
    coefficient_constante = serializers.FloatField(default=0.57)
    coefficient_r1 = serializers.FloatField(default=0.0535)
    coefficient_r2 = serializers.FloatField(default=0.0115)
    coefficient_r3 = serializers.FloatField(default=0.0371)
    coefficient_r4 = serializers.FloatField(default=0.0246)
    coefficient_r5 = serializers.FloatField(default=0.0115)
    coefficient_r6 = serializers.FloatField(default=0.0096)
    
    
    
    
    
    
    
# Serializers pour le scoring avec bilan classique
class BilanClassiqueScoreSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField(required=True)
    annee_n = serializers.IntegerField(required=True)
    annee_n1 = serializers.IntegerField(required=True)
    annee_n2 = serializers.IntegerField(required=True)
    bilan_type = serializers.CharField(default='classique')

class BilanClassiqueDataSerializer(serializers.Serializer):
    # Données extraites pour le calcul
    frais_financiers = serializers.DecimalField(max_digits=15, decimal_places=2)
    ebe = serializers.DecimalField(max_digits=15, decimal_places=2)
    creances_disponibilites = serializers.DecimalField(max_digits=15, decimal_places=2)
    dettes_court_terme = serializers.DecimalField(max_digits=15, decimal_places=2)
    capitaux_permanents = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_passif = serializers.DecimalField(max_digits=15, decimal_places=2)
    valeur_ajoutee = serializers.DecimalField(max_digits=15, decimal_places=2)
    chiffre_affaires = serializers.DecimalField(max_digits=15, decimal_places=2)
    tresorerie = serializers.DecimalField(max_digits=15, decimal_places=2)
    fonds_roulement = serializers.DecimalField(max_digits=15, decimal_places=2)

class ScoreACREMACResultSerializer(serializers.Serializer):
    score = serializers.FloatField()
    ratios = serializers.DictField()
    ratios_bornees = serializers.DictField()
    classe_risque = serializers.CharField()
    probabilite_defaillance = serializers.FloatField()
    commentaire = serializers.CharField()
    coefficients = serializers.DictField()

class BilanClassiqueScoreResponseSerializer(serializers.Serializer):
    acheteur = serializers.CharField()
    annees = serializers.DictField()
    scores = serializers.DictField()
    score_principal = serializers.FloatField()
    bilan_type = serializers.CharField()
    
    
    







from rest_framework import serializers

class BilanAnglaisScoreSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField(required=True)
    annee_n = serializers.IntegerField(required=True)
    annee_n1 = serializers.IntegerField(required=True)
    annee_n2 = serializers.IntegerField(required=True)
    bilan_type = serializers.CharField(default='anglais')

class BilanAnglaisDataSerializer(serializers.Serializer):
    # Données extraites pour le calcul ACREMAC
    frais_financiers = serializers.DecimalField(max_digits=15, decimal_places=2)
    ebe = serializers.DecimalField(max_digits=15, decimal_places=2)
    creances_disponibilites = serializers.DecimalField(max_digits=15, decimal_places=2)
    dettes_court_terme = serializers.DecimalField(max_digits=15, decimal_places=2)
    capitaux_permanents = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_passif = serializers.DecimalField(max_digits=15, decimal_places=2)
    valeur_ajoutee = serializers.DecimalField(max_digits=15, decimal_places=2)
    chiffre_affaires = serializers.DecimalField(max_digits=15, decimal_places=2)
    tresorerie = serializers.DecimalField(max_digits=15, decimal_places=2)
    fonds_roulement = serializers.DecimalField(max_digits=15, decimal_places=2)

class BilanAnglaisScoreResponseSerializer(serializers.Serializer):
    acheteur = serializers.CharField()
    annees = serializers.DictField()
    scores = serializers.DictField()
    score_principal = serializers.FloatField()
    bilan_type = serializers.CharField()
    
    
    
    
    
    
    
    
    
# serializers.py - Ajoutez ces sérialiseurs

class AssetsBancaireSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    a_vue = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    pret_interbancaire = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    porteuille_papier_commercial = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    autres_concours_clients = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    creance_sur_la_clientele = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_assets = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = Assets
        fields = '__all__'

class AddAssetsBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            'caisse', 'banques_centrales', 'tresorerie_cpp', 'autres_ets_credit',
            'a_terme', 'credits_campagne', 'credits_ordinaire', 
            'credits_campagne_acc', 'credits_ordinaire_acc', 'creances_ordinaires',
            'affacturage', 'titres_placement', 'immobilisation_fin',
            'operation_credit_bail', 'immobilisation_incorporelle',
            'immobilisation_corporelle', 'actionnaire_ou_associe',
            'autres_actifs', 'comptes_commande_divers'
        ]

class LiabilitiesBancaireSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    a_vue = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    dette_interbancaire = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    dette_envers_clientelle = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_liabilities = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = Liabilities
        fields = '__all__'

class AddLiabilitiesBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liabilities
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            'tresorerie_ccp', 'autres_etablissement_credit', 'a_terme',
            'comptes_epargne_court_terme', 'comptes_epargne_terme', 'bons_caisse',
            'autres_dette_a_vue', 'autres_dette_a_terme', 'titres_creance_autres_dettes',
            'compte_dordre_divers', 'provision_pour_risque_charge', 'provision_reglementee',
            'emprunt_subordonne_tire_emis', 'subventions_investissement', 'fonds_affecte',
            'fonds_pour_risque_bancaire_generaux', 'capital_ou_dotation',
            'primes_liees_reserve_capital', 'ecarts_reevaluation', 'benefices_non_distribue',
            'resultat_net_exercie'
        ]

class ExpensesBancaireSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    interet_charges_assimilee = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    charge_sur_operation_financiere = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    prestation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    frais_generaux_dexploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_des_charges = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = Expenses
        fields = '__all__'

class AddExpensesBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            'interet_charges_assimilee_dette_interbancaire',
            'interet_charge_assimilee_dette_clientele',
            'interet_charge_assimilee_titre_creance',
            'chargesc_compte_bloque_dactionnaire_emprunt_sub',
            'autres_interets_charges_assimilee',
            'charges_sur_op_credit_bail_assimile', 'commissions',
            'charges_sur_titre_placement', 'charges_sur_operation_change',
            'charges_sur_operation_hors_bilan', 'frais_divers_exploitation_bancaire',
            'achat_marchandises', 'stocks_vendus', 'variations_stocks_marchanides',
            'frais_personnel', 'autres_frais_generaux',
            'dotations_amortissement_provision_immobilisation',
            'solde_perte_creance_hors_bilan',
            'excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux',
            'charges_exceptionnelle', 'pertes_exercice_anterieurs', 'impot_sur_revenu'
        ]

class ProductsBancaireSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    interet_produit_assimile = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    revenu_d_operation_financiere = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    autres_produits_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_produit = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = Products
        fields = '__all__'

class AddProductsBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            'interets_produit_assimile_sur_pret_avance_interbancaire',
            'ineterets_produit_assimile_pret_avance_clientele',
            'interet_produit_sur_titre_dinvestissement',
            'revenu_gains_titre_pret_titre_subordonne',
            'autres_interets_produits_assimiles',
            'produits_leansing_operation_connexes', 'commissions',
            'revenus_titre_negociable', 'dividendes_produits_assimiles',
            'revenus_operation_de_change', 'produits_opeations_hors_bilan',
            'produits_bancaire_divers', 'marges_vente', 'ventes_marchandises',
            'variation_stocks_marchandises', 'produit_dexploitation_generale',
            'reprise_damortissement_provisions_sur_immobilisation',
            'solde_resultat_correction_valeur_sur_creance_hors_bilan',
            'excedent_reprise_fonds_pour_risque_bancaire_generaux',
            'produits_exceptionnels', 'benefice_sur_exercice_anterieur', 'perte'
        ]

class OffBalanceSheetBancaireSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    total_engagement_financement_donne = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_engagement_garantie_donne = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_engagements_donnes = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_engagement_financement_recu = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_engagements_recus = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = OffBalanceSheet
        fields = '__all__'

class AddOffBalanceSheetBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffBalanceSheet
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            'engagement_financement_donne_ets_credit',
            'engagement_financement_donne_clientele',
            'engagement_garantie_donne_ets_credit',
            'engagement_garantie_donne_clientele',
            'engagement_sur_titres_donnes',
            'engagement_financement_recu_ets_credit',
            'engagement_financement_recu_clientele',
            'engagement_garantie_recu_ets_credit',
            'engagement_sur_titres_recus'
        ]

# Serializer pour le calcul de score
class BilanBancaireScoreSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField()
    annee_n = serializers.IntegerField()
    annee_n1 = serializers.IntegerField()
    annee_n2 = serializers.IntegerField()
    bilan_type = serializers.ChoiceField(choices=TYPE_BILAN_CHOICES)
    semestre = serializers.ChoiceField(choices=SEMESTRE_CHOICES, required=False, allow_null=True)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
# serializers.py - Ajoutez ces sérialiseurs

class BilanSyscohadaScoreSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField()
    annee_n = serializers.IntegerField()
    annee_n1 = serializers.IntegerField()
    annee_n2 = serializers.IntegerField()

class ActifSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    immobilisations_incorporelles = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    immobilisations_corporelles = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    immobilisations_financieres = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif_immobilise = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    creances_emplois_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_tresorerie_equivalents = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif_circulant = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ActifS
        fields = '__all__'

class PassifSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    total_capitaux_propres_ressources_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_dettes_financieres_ressources_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_ressources_stables = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passifs_courants = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_tresorerie_equivalents = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passifs = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = PassifS
        fields = '__all__'

class ResultatSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    marge_commerciale = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    chiffre_affaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    valeur_ajoutee = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    excedent_brute_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_financier = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_activites_ordinaires_xe = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_activites_ordinaires_tn = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_net = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ResultatS
        fields = '__all__'
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
# serializers.py - Ajoutez ces sérialiseurs

class BilanIFRSScoreSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField()
    annee_n = serializers.IntegerField()
    annee_n1 = serializers.IntegerField()
    annee_n2 = serializers.IntegerField()

class ActifIFRSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    total_actif_non_courant = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_actif_courant = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_actif = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = ActifIFRS
        fields = '__all__'

class PassifIFRSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    total_capitaux_propres = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_passif_non_courant = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_passif_courant = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_passif = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = PassifIFRS
        fields = '__all__'

class ResultatIFRSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = CustomUserSerializer(read_only=True)
    updated_by = CustomUserSerializer(read_only=True)
    
    # Propriétés calculées
    chiffre_affaires = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    cout_des_ventes = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    charges_operationnelles = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    amortissements_et_provisions = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_charges = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    resultat_operationnel = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    resultat_financier = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    resultat_avant_impot = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    resultat_net = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = ResultatIFRS
        fields = '__all__'