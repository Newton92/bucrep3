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
    province = ProvinceSerializer()  # Utilisez le sérialiseur pour inclure les détails du pays
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'code', 'province', 'date_creation', 'date_modification', 'is_active']
        read_only_fields = ['id', 'date_creation', 'date_modification']
    
    
class VilleProvinceSerializer(serializers.ModelSerializer):
    province = ProvinceSerializer()  # Utilisez le sérialiseur pour inclure les détails du pays
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'code', 'province', 'date_creation', 'date_modification', 'is_active']
        read_only_fields = ['id', 'date_creation', 'date_modification']
    
    
class AddVilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'code', 'province', 'date_creation', 'date_modification', 'is_active']
        read_only_fields = ['id', 'date_creation', 'date_modification']
    
    
class UpdateVilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'code', 'province', 'date_creation', 'date_modification', 'is_active']
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


class DomaineEntrepriseSerializer(serializers.ModelSerializer):

    class Meta:
        model = DomaineEntreprise
        fields = ["id", "code", "libelle", "description", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        
class AddPosteEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosteEntreprise
        fields = ["id", "code", "libelle", "description", "domaine", "active", "created_at", "updated_at"]
        
class EditPosteEntrepriseSerializer(serializers.ModelSerializer):
    domaine = DomaineEntrepriseSerializer()
    class Meta:
        model = PosteEntreprise
        fields = ["id", "code", "libelle", "description", "domaine", "active", "created_at", "updated_at"]
        
class PosteEntrepriseSerializer(serializers.ModelSerializer):
    domaine = DomaineEntrepriseSerializer()
    class Meta:
        model = PosteEntreprise
        fields = ["id", "code", "libelle", "description", "domaine", "active", "created_at", "updated_at"]
        
        




class BaseModeleSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%d/%m/%Y")
    updated_at = serializers.DateTimeField(format="%d/%m/%Y")

    class Meta:
        fields = ["id", "code", "libelle", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


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


class ModeleNotationSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleNotation


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





        
        
class CategorieEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieEntreprise
        fields = ["id", "code", "libelle", "description", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class StructureEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = StructureEntreprise
        fields = ["id", "code", "libelle", "description", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class StatutEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatutEntreprise
        fields = ["id", "code", "libelle", "description", "active", "created_at", "updated_at"]
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
            "id", "code", 
            "categorie_entreprise", "forme_juridique", "activite_principale", 
            "nom", "sigle", 
            "description", "date_creation", "statut_entreprise", 
            "code_postal", "fax", "boite_postale", "email", "site_internet", "numero_adresse", "rue_adresse", 
            "ville", "province", "pays", "couleur_commentaire", "commentaire", 
            "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class AddAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Acheteur
        fields = [
            "id", "categorie_entreprise", "forme_juridique", "activite_principale", "nom", "sigle", "description",  
            "date_creation", "statut_entreprise",
            "code_postal", "fax", "boite_postale", "email", "site_internet", "numero_adresse", "rue_adresse", 
            "ville", "province", "pays", "couleur_commentaire", "commentaire"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class EditAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Acheteur
        fields = [
            "id", "code", "categorie_entreprise", "forme_juridique", "activite_principale", "nom", "sigle", "description", 
            "date_creation", "statut_entreprise",
            "code_postal", "fax", "boite_postale", "email", "site_internet", "numero_adresse", "rue_adresse", 
            "ville", "province", "pays", "couleur_commentaire", "commentaire"]
        read_only_fields = ["created_at", "updated_at"]
        
        
class GetAcheteurSerializer(serializers.ModelSerializer):
    categorie_entreprise = CategorieEntrepriseSerializer()
    forme_juridique = FormeJuridiqueSerializer()
    statut_entreprise = StatutEntrepriseSerializer()
    
    pays = PaysSerializer()
    province = ProvinceSerializer()
    ville = VilleSerializer()
    
    class Meta:
        model = Acheteur
        fields = [
            "id", "code", "categorie_entreprise", "forme_juridique", "activite_principale", "nom", "sigle", "description", 
            "date_creation", "statut_entreprise",
            "code_postal", "fax", "boite_postale", "email", "site_internet", "numero_adresse", "rue_adresse", 
            "ville", "province", "pays", "couleur_commentaire", "commentaire"]
        read_only_fields = ["created_at", "updated_at"]
        
        
        

class RiskRatingSerializer(serializers.ModelSerializer):
    
    acheteur = AcheteurSerializer()
    class Meta:
        model = RiskRating
        fields = '__all__'
        
        
class GetRiskRatingSerializer(serializers.ModelSerializer):
    
    acheteur = AcheteurSerializer()
    class Meta:
        model = RiskRating
        fields = '__all__'
        
        
class AddRiskRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskRating
        fields = [
            "id", "acheteur", "remboursabilite", "situation_liquidite", "performance_rentabilite", "perspective_secteur", 
            "qualite_information_analyse", "existence_garantie", 
            "terme_financier_duree_pret", "mesure_propre_soutenir_credit", "interpretation", "analyse"]
        
        
class EditRiskRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskRating
        fields = [
            "id", "acheteur", "remboursabilite", "situation_liquidite", "performance_rentabilite", "perspective_secteur", 
            "qualite_information_analyse", "existence_garantie", 
            "terme_financier_duree_pret", "mesure_propre_soutenir_credit", "interpretation", "analyse"]
        
        


class ResumeSerializer(serializers.ModelSerializer):
    
    acheteur = AcheteurSerializer()
    devise = DeviseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()
    
    class Meta:
        model = Resume
        fields = '__all__'
        
        
class AddResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            "id", "acheteur", "devise", "capital_social", "chiffre_affaire", "resultat_net", "capitaux_propre", "nombre_employe", 
            "date_creation", "couleur_commentaire", "commentaire"]
   
        
class GetResumeSerializer(serializers.ModelSerializer):
    
    acheteur = AcheteurSerializer()
    devise = DeviseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()
    
    class Meta:
        model = Resume
        fields = '__all__'
    
        
class EditResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            "id", "acheteur", "devise", "capital_social", "chiffre_affaire", "resultat_net", "capitaux_propre", "nombre_employe", 
            "date_creation", "couleur_commentaire", "commentaire"]




class DonneesEnregistrementSerializer(serializers.ModelSerializer):
    forme_juridique_ref = FormeJuridiqueSerializer()
    statut_registre_ref = StatutEntrepriseSerializer()
    class Meta:
        model = DonneesEnregistrement
        fields = '__all__'
        
        
class GetDonneesEnregistrementSerializer(serializers.ModelSerializer):
    forme_juridique_ref = FormeJuridiqueSerializer()
    statut_registre_ref = StatutEntrepriseSerializer()
    class Meta:
        model = DonneesEnregistrement
        fields = '__all__'  
        
        
class AddDonneesEnregistrementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonneesEnregistrement   
        fields = [
            "id", "acheteur", "date_creation", "date_registre", "forme_juridique", "forme_juridique_ref", "numero_registre_commerce", "numero_fiscale", 
            "statut_registre", "statut_registre_ref", "commentaire"]
        
        
class EditDonneesEnregistrementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonneesEnregistrement   
        fields = [
            "id", "acheteur", "date_creation", "date_registre", "forme_juridique", "forme_juridique_ref", "numero_registre_commerce", "numero_fiscale", 
            "statut_registre", "statut_registre_ref", "commentaire"]     











class TendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tendance
        fields = '__all__'

class ResponsableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponsableAcheteur
        fields = '__all__'

class AntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedantsJuridique
        fields = '__all__'

class RiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = '__all__'

class ConseilAdministrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConseilAdministration
        fields = '__all__'

class CompositionCapitalSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionCapitalSocial
        fields = '__all__'

class CompositionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionAction
        fields = '__all__'
