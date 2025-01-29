# main/serializers.py
from rest_framework import serializers
from .models import *

# Vos serializers ici !

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'avatar', 'code_secret', 'adresse', 'activation', 'auth_a2f', 'telephone', 'profession', 'email_cc']


class PaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pays
        fields = ['id', 'nom', 'code', 'afficher_au_dashboard', 'is_active', 'date_creation', 'date_modification']
        read_only_fields = ['id', 'date_creation', 'date_modification']
        
        
class ProvinceSerializer(serializers.ModelSerializer):
    pays = PaysSerializer()  # Utilisez le sérialiseur pour inclure les détails du pays
    class Meta:
        model = Province
        fields = ['id', 'nom', 'code', 'pays', 'date_creation', 'date_modification', 'is_active']
        read_only_fields = ['id', 'date_creation', 'date_modification']
        
        
class AddProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'nom', 'code', 'pays', 'date_creation', 'date_modification', 'is_active']
        read_only_fields = ['id', 'date_creation', 'date_modification']
        
        
class UpdateProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'nom', 'code', 'pays', 'date_creation', 'date_modification', 'is_active']
        read_only_fields = ['id', 'date_creation', 'date_modification']
    
    
class VilleSerializer(serializers.ModelSerializer):
    pays = PaysSerializer()  # Utilisez le sérialiseur pour inclure les détails du pays
    province = ProvinceSerializer()  # Utilisez le sérialiseur pour inclure les détails du pays
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'code', 'pays', 'province', 'date_creation', 'date_modification', 'is_active']
        read_only_fields = ['id', 'date_creation', 'date_modification']
    
    
class AddVilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'code', 'pays', 'province', 'date_creation', 'date_modification', 'is_active']
        read_only_fields = ['id', 'date_creation', 'date_modification']
    
    
class UpdateVilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'code', 'pays', 'province', 'date_creation', 'date_modification', 'is_active']
        read_only_fields = ['id', 'date_creation', 'date_modification']
        
        
class AnneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annee
        fields = "__all__"  # Inclut tous les champs du modèle
        read_only_fields = ["date_creation", "date_modification"]  # Ces champs seront uniquement en lecture
        
        
class DeviseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devise
        fields = "__all__"  # Inclut tous les champs du modèle
        read_only_fields = ["date_creation", "date_modification"]  # Ces champs seront uniquement en lecture
        
        
class CouleurCommentaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouleurCommentaire
        fields = ['id', 'couleur', 'code']
        
        


class AddCategoryNaceCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class AddSubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoryNaceCode
        fields = ["id", "category", "code", "libelle", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class CategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ['id', 'code', 'libelle']
        
        
class EditSubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    category = CategoryNaceCodeSerializer()
    class Meta:
        model = SubCategoryNaceCode
        fields = ["id", "category", "code", "libelle", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class SubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    category = CategoryNaceCodeSerializer()

    class Meta:
        model = SubCategoryNaceCode
        fields = ['id', 'category', 'code', 'libelle', 'active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class CategoryNaceCodeSerializer(serializers.ModelSerializer):
    subcategories = SubCategoryNaceCodeSerializer(many=True, read_only=True)

    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "active", "created_at", "updated_at", "subcategories"]
        read_only_fields = ["created_at", "updated_at"]
        
        
        
        
class AddSubCategoryNafCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoryNafCode
        fields = ["id", "category", "code", "libelle", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"] 
             





class CategoryNafCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CategoryNafCode
        fields = ["id", "code", "libelle", "active", "created_at", "updated_at", "subcategories"]
        read_only_fields = ["created_at", "updated_at"]        
        
class SubCategoryNafCodeSerializer(serializers.ModelSerializer):
    category = CategoryNafCodeSerializer()
    class Meta:
        model = SubCategoryNafCode
        fields = ["id", "category", "code", "libelle", "active", "created_at", "updated_at"]
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
        fields = ["id", "code", "libelle", "active", "created_at", "updated_at", "subcategories"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class EditSubCategoryNafCodeSerializer(serializers.ModelSerializer):
    category = CategoryNafCodeSerializer()
    class Meta:
        model = SubCategoryNafCode
        fields = ["id", "category", "code", "libelle", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class FormeJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormeJuridique
        fields = ["id", "code", "libelle", "description", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        
class PosteEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosteEntreprise
        fields = ["id", "code", "libelle", "description", "active", "created_at", "updated_at"]


class DomaineEntrepriseSerializer(serializers.ModelSerializer):
    postes = PosteEntrepriseSerializer(many=True, read_only=True)

    class Meta:
        model = DomaineEntreprise
        fields = ["id", "code", "libelle", "description", "active", "postes", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class BaseModeleSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'code', 'libelle', 'created_at', 'updated_at']

class ModeleRapportSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleRapport

class ModeleAvisCommercialSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleAvisCommercial

class ModeleAlarmeSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleAlarme

class ModeleBilanSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleBilan

class ModeleBailSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleBail

class ModeleRelationEntrepriseSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleRelationEntreprise

class ModeleInformationNotationEntrepriseSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleInformationNotationEntreprise

class ModeleComportementPaiementSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleComportementPaiement

class ModeleComportementJugementSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleComportementJugement
        
        
