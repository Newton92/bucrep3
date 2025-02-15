# main/serializers.py
from rest_framework import serializers
from django.core.exceptions import ValidationError
import decimal
from django.utils import timezone
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

    def validate_capital_social(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_chiffre_affaire(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_resultat_net(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_capitaux_propres(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_nombre_employe(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

        
        
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
    acheteur = AcheteurSerializer()
    forme_juridique_ref = FormeJuridiqueSerializer()
    statut_registre_ref = StatutEntrepriseSerializer()

    class Meta:
        model = DonneesEnregistrement
        fields = '__all__'

        
        
class GetDonneesEnregistrementSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
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
    acheteur = AcheteurSerializer()
    avis_commercial_ref = ModeleAvisCommercialSerializer()
    class Meta:
        model = Tendance
        fields = '__all__'
        
        
class GetTendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tendance
        fields = '__all__'
        
        
class AddTendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tendance
        fields = [
            "id", "acheteur", "avis_commercial", "avis_commercial_ref", "presse_media", "principaux_concurrent", "commentaire"]  
        
        
class EditTendanceSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    avis_commercial_ref = ModeleAvisCommercialSerializer()
    class Meta:
        model = Tendance
        fields = [
            "id", "acheteur", "avis_commercial", "avis_commercial_ref", "presse_media", "principaux_concurrent", "commentaire"]  
        
        
        




class ResponsableAcheteurSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    poste_ref = PosteEntrepriseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()
    class Meta:
        model = ResponsableAcheteur
        fields = '__all__'
        
        
class GetResponsableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponsableAcheteur
        fields = '__all__'
        
        
class AddResponsableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponsableAcheteur
        fields = [
            "id", "acheteur", "nom", "prenom", "sexe", "poste", "poste_ref", "nationalite", "couleur_commentaire", "commentaire"] 
        
        
class EditResponsableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponsableAcheteur
        fields = [
            "id", "acheteur", "nom", "prenom", "sexe", "poste", "poste_ref", "nationalite", "couleur_commentaire", "commentaire"] 
        
        
        



        

class AntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()
    class Meta:
        model = AntecedantsJuridique
        fields = '__all__'
        
        
class GetAntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedantsJuridique
        fields = '__all__'
        
        
class AddAntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedantsJuridique
        fields = [
            "id", "acheteur", "dossier_faillite", "jugement_cour", "antecedant_redressement", "autre", "couleur_commentaire", "commentaire"] 
        
        
class EditAntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedantsJuridique
        fields = [
            "id", "acheteur", "dossier_faillite", "jugement_cour", "antecedant_redressement", "autre", "couleur_commentaire", "commentaire"] 
        
        
        
        
        
        

class RiskManagmentSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()
    class Meta:
        model = RiskManagment
        fields = '__all__'
        
        
class GetRiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = '__all__'
        
        
class AddRiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = [
            "id", "acheteur", "professionalisme", "organisation", "turn_over", "greve", 
            "degradation_qualite", "non_respect_condition", "couleur_commentaire", "commentaire"] 
        
        
class EditRiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = [
            "id", "acheteur", "professionalisme", "organisation", "turn_over", "greve", 
            "degradation_qualite", "non_respect_condition", "couleur_commentaire", "commentaire"]          
        
        
   
   
   
   

   
        
        

class ConseilAdministrationSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    fonction_dans_le_conseil_ref = PosteEntrepriseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()
    class Meta:
        model = ConseilAdministration
        fields = '__all__'
        
        
class GetConseilAdministrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConseilAdministration
        fields = '__all__'
        
        
class AddConseilAdministrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConseilAdministration
        fields = [
            "id", "acheteur", "nom", "fonction_dans_le_conseil", "fonction_dans_le_conseil_ref", "numero_adresse", "rue_adresse", 
            "code_postale_adresse", "couleur_commentaire", "commentaire"] 
        
        
class EditConseilAdministrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConseilAdministration
        fields = [
            "id", "acheteur", "nom", "fonction_dans_le_conseil", "fonction_dans_le_conseil_ref", "numero_adresse", "rue_adresse", 
            "code_postale_adresse", "couleur_commentaire", "commentaire"] 
        
        
        
        
        
        
        
        
        

class CompositionCapitalSocialSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    devise = DeviseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()
    class Meta:
        model = CompositionCapitalSocial
        fields = '__all__'
        
        
class GetCompositionCapitalSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionCapitalSocial
        fields = '__all__'
        
        
class AddCompositionCapitalSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionCapitalSocial
        fields = [
            "id", "acheteur", "devise", "emis", "publie", "libere", "couleur_commentaire", "commentaire"] 
        
        
class EditCompositionCapitalSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionCapitalSocial
        fields = [
            "id", "acheteur", "devise", "emis", "publie", "libere", "couleur_commentaire", "commentaire"] 
        
        
        
        
        
        
        
       

class CompositionActionSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()
    class Meta:
        model = CompositionAction
        fields = '__all__'
        
        
class GetCompositionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionAction
        fields = '__all__'
        
        
class AddCompositionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionAction
        fields = [
            "id", "acheteur", "nom", "prenom", "pourcentage", "couleur_commentaire", "commentaire"] 
        
        
class EditCompositionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionAction
        fields = [
            "id", "acheteur", "nom", "prenom", "pourcentage", "couleur_commentaire", "commentaire"] 







class OpinionCreditAcremacSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = OpinionCreditAcremac
        fields = '__all__'
        
        
class GetOpinionCreditAcremacSerializer(serializers.ModelSerializer):

    class Meta:
        model = OpinionCreditAcremac
        fields = '__all__'
        
        

class AddOpinionCreditAcremacSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpinionCreditAcremac
        fields = [
            'acheteur', 'risque_de_defaut', 'risque_de_concentration_credit', 'risque_de_reputation',
            'risque_pays', 'risque_de_taux_dinteret', 'risque_de_liquidite', 'risque_eleve',
            'risque_moyen', 'risque_faible', "couleur_commentaire", "commentaire"
        ]

class EditOpinionCreditAcremacSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpinionCreditAcremac
        fields = [
            'acheteur', 'risque_de_defaut', 'risque_de_concentration_credit', 'risque_de_reputation',
            'risque_pays', 'risque_de_taux_dinteret', 'risque_de_liquidite', 'risque_eleve',
            'risque_moyen', 'risque_faible', "couleur_commentaire", "commentaire"
        ]










class StructureSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()
    type_affiliation_ref = StructureEntrepriseSerializer()

    class Meta:
        model = Structure
        fields = '__all__'

class GetStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Structure
        fields = '__all__'

class AddStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Structure
        fields = [
            'acheteur', 'nom', 'type_affiliation', 'type_affiliation_ref',
            'numero_adresse', 'rue_adresse', 'code_postale_adresse',
            'couleur_commentaire', 'commentaire'
        ]

class EditStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Structure
        fields = [
            'acheteur', 'nom', 'type_affiliation', 'type_affiliation_ref',
            'numero_adresse', 'rue_adresse', 'code_postale_adresse',
            'couleur_commentaire', 'commentaire'
        ]







class AnalyseSectorielleSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = AnalyseSectorielle
        fields = '__all__'

class GetAnalyseSectorielleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseSectorielle
        fields = '__all__'

class AddAnalyseSectorielleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseSectorielle
        fields = [
            'acheteur', 'couleur_commentaire', 'commentaire', 'impact_covid_19'
        ]

class EditAnalyseSectorielleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseSectorielle
        fields = [
            'acheteur', 'couleur_commentaire', 'commentaire', 'impact_covid_19'
        ]











class CompteFinancierSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    type_bilan_ref = ModeleBilanSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = CompteFinancier
        fields = '__all__'
        
        
class GetCompteFinancierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancier
        fields = '__all__'



class AddCompteFinancierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancier
        fields = [
            'acheteur', 'cabinet', 'requis_pour_deposer', 'credibilite_cabinet',
            'source', 'presentation', 'date_compte', 'date_fin',
            'date_compte_n_moins_un', 'date_fin_n_moins_un',
            'date_compte_n_moins_deux', 'date_fin_n_moins_deux',
            'type_compte', 'devise', 'type_bilan', 'type_bilan_ref', 'couleur_commentaire', 'commentaire'
        ]



class EditCompteFinancierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancier
        fields = [
            'acheteur', 'cabinet', 'requis_pour_deposer', 'credibilite_cabinet',
            'source', 'presentation', 'date_compte', 'date_fin',
            'date_compte_n_moins_un', 'date_fin_n_moins_un',
            'date_compte_n_moins_deux', 'date_fin_n_moins_deux',
            'type_compte', 'devise', 'type_bilan', 'type_bilan_ref', 'couleur_commentaire', 'commentaire'
        ]









class OperationEtHistoriqueSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur

    class Meta:
        model = OperationEtHistorique
        fields = '__all__'

class GetOperationEtHistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationEtHistorique
        fields = '__all__'

class AddOperationEtHistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationEtHistorique
        fields = [
            'acheteur', 'commentaire_ratios', 'description_complete_activite',
            'importation', 'historique'
        ]

class EditOperationEtHistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationEtHistorique
        fields = [
            'acheteur', 'commentaire_ratios', 'description_complete_activite',
            'importation', 'historique'
        ]










class ProprieteEtActifSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    locaux_ref = ModeleBailSerializer()  # Utilisez un sérialiseur imbriqué pour la référence sur les locaux

    class Meta:
        model = ProprieteEtActif
        fields = '__all__'

class GetProprieteEtActifSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProprieteEtActif
        fields = '__all__'

class AddProprieteEtActifSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProprieteEtActif
        fields = [
            'acheteur', 'locaux', 'locaux_ref', 'branche'
        ]

class EditProprieteEtActifSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProprieteEtActif
        fields = [
            'acheteur', 'locaux', 'locaux_ref', 'branche'
        ]




class ConditionAchatSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur

    class Meta:
        model = ConditionAchat
        fields = '__all__'

class GetConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAchat
        fields = '__all__'

class AddConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAchat
        fields = ['acheteur', 'local', 'importation', 'les_clients', 'fournisseur']

class EditConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAchat
        fields = ['acheteur', 'local', 'importation', 'les_clients', 'fournisseur']
        
        
        






class ConditionDeVenteSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    recouvrement_de_dette_jugement_ref = ModeleComportementJugementSerializer()
    comportement_de_paiement_ref = ModeleComportementPaiementSerializer()

    class Meta:
        model = ConditionDeVente
        fields = '__all__'

class GetConditionDeVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionDeVente
        fields = '__all__'

class AddConditionDeVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionDeVente
        fields = [
            'acheteur', 'local', 'recouvrement_de_dette_jugement',
            'recouvrement_de_dette_jugement_ref', 'comportement_de_paiement',
            'comportement_de_paiement_ref'
        ]

class EditConditionDeVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionDeVente
        fields = [
            'acheteur', 'local', 'recouvrement_de_dette_jugement',
            'recouvrement_de_dette_jugement_ref', 'comportement_de_paiement',
            'comportement_de_paiement_ref'
        ]







class SommaireEtAvisSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = SommaireEtAvis
        fields = '__all__'

class GetSommaireEtAvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SommaireEtAvis
        fields = '__all__'

class AddSommaireEtAvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SommaireEtAvis
        fields = ['acheteur', 'couleur_commentaire', 'commentaire']

class EditSommaireEtAvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SommaireEtAvis
        fields = ['acheteur', 'couleur_commentaire', 'commentaire']
        
        
        





class AdviceSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur

    class Meta:
        model = Advice
        fields = '__all__'

class GetAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = '__all__'

class AddAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = ['acheteur', 'points_forts', 'points_faibles', 'dynamisme_court_terme', 'dynamisme_long_terme']

class EditAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = ['acheteur', 'points_forts', 'points_faibles', 'dynamisme_court_terme', 'dynamisme_long_terme']




class GeopoliticsSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur

    class Meta:
        model = Geopolitics
        fields = '__all__'

class GetGeopoliticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geopolitics
        fields = '__all__'

class AddGeopoliticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geopolitics
        fields = ['acheteur', 'donnees_politiques', 'donnees_economiques']

class EditGeopoliticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geopolitics
        fields = ['acheteur', 'donnees_politiques', 'donnees_economiques']
        
        
        



class BanquierSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    ville = VilleSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = Banquier
        fields = '__all__'

class GetBanquierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banquier
        fields = '__all__'

class AddBanquierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banquier
        fields = ['acheteur', 'nom_banque', 'numero_compte', 'type_relation', 'numero', 'rue', 'ville', 'code_postal', 'couleur_commentaire', 'commentaire']

class EditBanquierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banquier
        fields = ['acheteur', 'nom_banque', 'numero_compte', 'type_relation', 'numero', 'rue', 'ville', 'code_postal', 'couleur_commentaire', 'commentaire']
