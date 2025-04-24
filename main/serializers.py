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
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'avatar', 'code_secret', 'address', 'activation', 'auth_a2f', 'telephone', 'profession', 'email_cc']


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


class ModeleAvisCommercialSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleAvisCommercial


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
            'risque_moyen', 'risque_faible', "couleur_commentaire", "montant_credit_maximum", "commentaire"
        ]


class EditOpinionCreditAcremacSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpinionCreditAcremac
        fields = [
            'acheteur', 'risque_de_defaut', 'risque_de_concentration_credit', 'risque_de_reputation',
            'risque_pays', 'risque_de_taux_dinteret', 'risque_de_liquidite', 'risque_eleve',
            'risque_moyen', 'risque_faible', "couleur_commentaire", "montant_credit_maximum", "commentaire"
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







class ActifASerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ActifA
        fields = '__all__'

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
            "id", "annee", "acheteur", "biens_installations_equipements", "inventaire",
            "creances_commerciales_autres_creances", "actif_impots_courant", "caisses_banques",
            "created_by", "updated_by"
        ]

class GetActifASerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = ActifA
        fields = '__all__'

class EditActifASerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifA
        fields = [
            "id", "annee", "acheteur", "biens_installations_equipements", "inventaire",
            "creances_commerciales_autres_creances", "actif_impots_courant", "caisses_banques",
            "created_by", "updated_by"
        ]







class PassifASerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = PassifA
        fields = '__all__'

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
            "id", "annee", "acheteur", "capital_reserves", "capital_declare",
            "benefices_non_distribues", "pret_bancaire", "compte_courant_administrateurs",
            "dettes_commerciales_autres_dettes", "decouvert_bancaire", "impots",
            "created_by", "updated_by"
        ]

class GetPassifASerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = PassifA
        fields = '__all__'

class EditPassifASerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifA
        fields = [
            "id", "annee", "acheteur", "capital_reserves", "capital_declare",
            "benefices_non_distribues", "pret_bancaire", "compte_courant_administrateurs",
            "dettes_commerciales_autres_dettes", "decouvert_bancaire", "impots",
            "created_by", "updated_by"
        ]










class ResultatASerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ResultatA
        fields = '__all__'

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
            "id", "annee", "acheteur", "produits_activites_ordinaires", "ventes",
            "charges_exploitation", "frais_vente_generaux_administratifs",
            "autres_revenus", "frais_financier", "charge_impot_sur_revenu",
            "autres_elements_resultat_global", "created_by", "updated_by"
        ]

class GetResultatASerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = ResultatA
        fields = '__all__'

class EditResultatASerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatA
        fields = [
            "id", "annee", "acheteur", "produits_activites_ordinaires", "ventes",
            "charges_exploitation", "frais_vente_generaux_administratifs",
            "autres_revenus", "frais_financier", "charge_impot_sur_revenu",
            "autres_elements_resultat_global", "created_by", "updated_by"
        ]










class ActifCSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ActifC
        fields = '__all__'

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
            "id", "annee", "acheteur", "capital_souscrit_non_app", "frais_recherche_developpement",
            "brevet_licence_logiciels", "fonds_commercial", "autres_immobilisations_incorporelles",
            "terrains", "constructions", "materiels_et_outils", "materiel_de_transport",
            "autres_immos_corp", "immos_en_cours", "avances_et_acptes", "participations",
            "prets", "autres", "stocks_mp", "stocks_encours_mp", "stocks_pf",
            "stocks_encours_pf", "stocks_encours_services", "stocks_mses", "avances_acptes_verses",
            "clients_et_cptes_rattaches", "autres_creances", "valeurs_a_encaisser",
            "banques_cheques_postaux_caisse", "cca", "charges_a_repartir_et_frais_etablissement",
            "primes_de_rbt", "eca", "eene", "effectif", "amortissements", "provisions_stocks",
            "provisions_creances", "provisions_vmp", "created_by", "updated_by"
        ]

class GetActifCSerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = ActifC
        fields = '__all__'

class EditActifCSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifC
        fields = [
            "id", "annee", "acheteur", "capital_souscrit_non_app", "frais_recherche_developpement",
            "brevet_licence_logiciels", "fonds_commercial", "autres_immobilisations_incorporelles",
            "terrains", "constructions", "materiels_et_outils", "materiel_de_transport",
            "autres_immos_corp", "immos_en_cours", "avances_et_acptes", "participations",
            "prets", "autres", "stocks_mp", "stocks_encours_mp", "stocks_pf",
            "stocks_encours_pf", "stocks_encours_services", "stocks_mses", "avances_acptes_verses",
            "clients_et_cptes_rattaches", "autres_creances", "valeurs_a_encaisser",
            "banques_cheques_postaux_caisse", "cca", "charges_a_repartir_et_frais_etablissement",
            "primes_de_rbt", "eca", "eene", "effectif", "amortissements", "provisions_stocks",
            "provisions_creances", "provisions_vmp", "created_by", "updated_by"
        ]











class PassifCSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = PassifC
        fields = '__all__'

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
            "id", "annee", "acheteur", "capital_social", "primes", "ecarts_de_reevaluation",
            "reserve", "report_a_nouveau", "resultat_exercice", "subv_invest",
            "provision_regl", "emprunts", "dette_credit_bail_contrat_assimile",
            "dettes_financiere_diverses", "provision_financiere_risque_charge",
            "dettes_fournisseurs_divers", "avance_et_acomptes_recu", "dettes",
            "dettes_fiscales_sociales", "autres_dettes", "banques_credit_escompte",
            "banque_credit_caisse", "banques_decouvert", "ecart_conversion_passif",
            "created_by", "updated_by"
        ]

class GetPassifCSerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = PassifC
        fields = '__all__'

class EditPassifCSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifC
        fields = [
            "id", "annee", "acheteur", "capital_social", "primes", "ecarts_de_reevaluation",
            "reserve", "report_a_nouveau", "resultat_exercice", "subv_invest",
            "provision_regl", "emprunts", "dette_credit_bail_contrat_assimile",
            "dettes_financiere_diverses", "provision_financiere_risque_charge",
            "dettes_fournisseurs_divers", "avance_et_acomptes_recu", "dettes",
            "dettes_fiscales_sociales", "autres_dettes", "banques_credit_escompte",
            "banque_credit_caisse", "banques_decouvert", "ecart_conversion_passif",
            "created_by", "updated_by"
        ]













class ResultatCSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ResultatC
        fields = '__all__'

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
            "id", "annee", "acheteur", "vente_de_mdses", "ventes_de_produits_fabriques",
            "travaux_services_vendus", "produit_accessoires", "production_imblise",
            "subventions_exploitations", "production_stockee", "reprises_de_provision",
            "transferts_charges", "autres_produits", "achat_mdses", "variation_stock_mdses",
            "achat_mp_autres_appro", "var_stk_mp_app", "autres_achats",
            "variation_de_stocks_autres_appro", "transports", "services_ext",
            "impots_taxes", "autres_charges_valeur_ajoutee", "charges_personnel",
            "dotation_aux_amorts", "dotation_aux_provisions", "autres_charges_excedent_brute",
            "revenus_fin_assimiles", "prof_vmp_et_cre_actif_immo", "interets_produit_assim",
            "reprise_prov_et_transfert", "diff_positive_de_change", "prod_nets_cessions_vmp",
            "dap", "frais_fin_charges_assi", "diff_negatives_de_change",
            "ch_nettes_cessions_vmp", "sur_op_gestion_prod_except", "sur_op_en_capital_prod_except",
            "reprise_prov_transfert", "sur_op_gestion_charg_except", "sur_op_en_capital_charg_except",
            "dap_et_transfert_charg_except", "participation_salairies", "impot_sur_benefices",
            "created_by", "updated_by"
        ]

class GetResultatCSerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = CustomUserSerializer()
    # updated_by = CustomUserSerializer()

    class Meta:
        model = ResultatC
        fields = '__all__'

class EditResultatCSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatC
        fields = [
            "id", "annee", "acheteur", "vente_de_mdses", "ventes_de_produits_fabriques",
            "travaux_services_vendus", "produit_accessoires", "production_imblise",
            "subventions_exploitations", "production_stockee", "reprises_de_provision",
            "transferts_charges", "autres_produits", "achat_mdses", "variation_stock_mdses",
            "achat_mp_autres_appro", "var_stk_mp_app", "autres_achats",
            "variation_de_stocks_autres_appro", "transports", "services_ext",
            "impots_taxes", "autres_charges_valeur_ajoutee", "charges_personnel",
            "dotation_aux_amorts", "dotation_aux_provisions", "autres_charges_excedent_brute",
            "revenus_fin_assimiles", "prof_vmp_et_cre_actif_immo", "interets_produit_assim",
            "reprise_prov_et_transfert", "diff_positive_de_change", "prod_nets_cessions_vmp",
            "dap", "frais_fin_charges_assi", "diff_negatives_de_change",
            "ch_nettes_cessions_vmp", "sur_op_gestion_prod_except", "sur_op_en_capital_prod_except",
            "reprise_prov_transfert", "sur_op_gestion_charg_except", "sur_op_en_capital_charg_except",
            "dap_et_transfert_charg_except", "participation_salairies", "impot_sur_benefices",
            "created_by", "updated_by"
        ]








class ActifSysCohadaSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ActifS
        fields = '__all__'

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
            "id", "annee", "acheteur", "frais_developpement_prospection", "brevets_licences_logiciels",
            "droits_propriete_commerciale_baux", "autres_immo_incorporelles", "terrains",
            "dons_investissements_net", "batiments", "agencements_amenagements_installations",
            "materiel_mobilier_actif_biologiques", "materiel_transport", "avances_acompte_immobilisations",
            "titres_participation", "autres_immobilisations_financieres", "actif_circulant_hao",
            "stock_encours", "fournisseurs_avances_versee", "clients", "autres_creances",
            "valeurs_mobilieres_placement", "disponibilites", "banque_cheque_postal_caisse_assimiles",
            "ecart_conversion_actif", "created_by", "updated_by"
        ]

class GetActifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = '__all__'

class EditActifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = [
            "id", "annee", "acheteur", "frais_developpement_prospection", "brevets_licences_logiciels",
            "droits_propriete_commerciale_baux", "autres_immo_incorporelles", "terrains",
            "dons_investissements_net", "batiments", "agencements_amenagements_installations",
            "materiel_mobilier_actif_biologiques", "materiel_transport", "avances_acompte_immobilisations",
            "titres_participation", "autres_immobilisations_financieres", "actif_circulant_hao",
            "stock_encours", "fournisseurs_avances_versee", "clients", "autres_creances",
            "valeurs_mobilieres_placement", "disponibilites", "banque_cheque_postal_caisse_assimiles",
            "ecart_conversion_actif", "created_by", "updated_by"
        ]








class PassifSysSCohadaSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = PassifS
        fields = '__all__'

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
            "id", "annee", "acheteur", "capital", "capital_non_appele_apporteurs", "primes_liees_capital_social",
            "ecart_reevaluation", "reserves_indisponibles", "reserves_libres", "report_nouveau",
            "resultat_net_exercice", "subventions_investissements", "provisions_reglees",
            "emprunts_dettes_financieres_diverse", "dettes_location_vente", "provisions_risques_charges",
            "passif_circulant_hao", "clients_avances_recues", "fournisseurs_exploitation",
            "dettes_fiscales_sociales", "autres_dettes", "provisions_risques_court_terme",
            "banques_credit_escompte", "banques_etablissements_financiers_credit_caisse",
            "ecart_conversion_passif", "created_by", "updated_by"
        ]

class GetPassifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = '__all__'

class EditPassifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = [
            "id", "annee", "acheteur", "capital", "capital_non_appele_apporteurs", "primes_liees_capital_social",
            "ecart_reevaluation", "reserves_indisponibles", "reserves_libres", "report_nouveau",
            "resultat_net_exercice", "subventions_investissements", "provisions_reglees",
            "emprunts_dettes_financieres_diverse", "dettes_location_vente", "provisions_risques_charges",
            "passif_circulant_hao", "clients_avances_recues", "fournisseurs_exploitation",
            "dettes_fiscales_sociales", "autres_dettes", "provisions_risques_court_terme",
            "banques_credit_escompte", "banques_etablissements_financiers_credit_caisse",
            "ecart_conversion_passif", "created_by", "updated_by"
        ]







class ResultatSysCohadaSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = ResultatS
        fields = '__all__'

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
            "id", "annee", "acheteur", "ventes_marchandises_a", "achats_marchandises", "variation_stock_marchandises",
            "ventes_produits_manufactures", "travaux_services_vendus_c", "produits_accessoires_d",
            "production_stockee", "production_immobilisee", "subvention_exploitation", "autres_produits",
            "transfert_charges_exploitation", "achats_matieres_premieres_fournitures_connexes",
            "variation_stock_matieres_premieres_fournitures_connexes", "autres_achats",
            "variation_stock_autres_fournitures", "transport", "services_exterieurs", "impots_taxes",
            "autres_depenses", "frais_personnel", "reprise_depreciations_amortissements_provision_pertes_valeurs_p",
            "reprise_depreciations_amortissements_provision_pertes_valeurs_m", "produits_financiers_assimiles",
            "reprise_provision_perte_valeur", "transfert_charges_financieres", 
            "dotations_provisions_depreciations_financieres", "produits_cession_immobilisations",
            "autres_produits_hao", "valeur_comptable_cessions_actifs_immobilises", "autres_charges_hao",
            "participation_travailleurs", "charge_impot_revenu", "created_by", "updated_by"
        ]

class GetResultatSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = '__all__'

class EditResultatSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = [
            "id", "annee", "acheteur", "ventes_marchandises_a", "achats_marchandises", "variation_stock_marchandises",
            "ventes_produits_manufactures", "travaux_services_vendus_c", "produits_accessoires_d",
            "production_stockee", "production_immobilisee", "subvention_exploitation", "autres_produits",
            "transfert_charges_exploitation", "achats_matieres_premieres_fournitures_connexes",
            "variation_stock_matieres_premieres_fournitures_connexes", "autres_achats",
            "variation_stock_autres_fournitures", "transport", "services_exterieurs", "impots_taxes",
            "autres_depenses", "frais_personnel", "reprise_depreciations_amortissements_provision_pertes_valeurs_p",
            "reprise_depreciations_amortissements_provision_pertes_valeurs_m", "produits_financiers_assimiles",
            "reprise_provision_perte_valeur", "transfert_charges_financieres", 
            "dotations_provisions_depreciations_financieres", "produits_cession_immobilisations",
            "autres_produits_hao", "valeur_comptable_cessions_actifs_immobilises", "autres_charges_hao",
            "participation_travailleurs", "charge_impot_revenu", "created_by", "updated_by"
        ]






class AssetsSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = Assets
        fields = '__all__'

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
            "id", "annee", "acheteur", "caisse", "banques_centrales", "tresorerie_cpp",
            "autres_ets_credit", "a_terme", "credits_campagne", "credits_ordinaire",
            "credits_campagne_acc", "credits_ordinaire_acc", "creances_ordinaires",
            "affacturage", "titres_placement", "immobilisation_fin", "operation_credit_bail",
            "immobilisation_incorporelle", "immobilisation_corporelle", "actionnaire_ou_associe",
            "autres_actifs", "comptes_commande_divers", "created_by", "updated_by"
        ]

class GetAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = '__all__'

class EditAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = [
            "id", "annee", "acheteur", "caisse", "banques_centrales", "tresorerie_cpp",
            "autres_ets_credit", "a_terme", "credits_campagne", "credits_ordinaire",
            "credits_campagne_acc", "credits_ordinaire_acc", "creances_ordinaires",
            "affacturage", "titres_placement", "immobilisation_fin", "operation_credit_bail",
            "immobilisation_incorporelle", "immobilisation_corporelle", "actionnaire_ou_associe",
            "autres_actifs", "comptes_commande_divers", "created_by", "updated_by"
        ]














class LiabilitiesSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = Liabilities
        fields = '__all__'

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
            "id", "annee", "acheteur", "tresorerie_ccp", "autres_etablissement_credit",
            "a_terme", "comptes_epargne_court_terme", "comptes_epargne_terme", "bons_caisse",
            "autres_dette_a_vue", "autres_dette_a_terme", "titres_creance_autres_dettes",
            "compte_dordre_divers", "provision_pour_risque_charge", "provision_reglementee",
            "emprunt_subordonne_tire_emis", "subventions_investissement", "fonds_affecte",
            "fonds_pour_risque_bancaire_generaux", "capital_ou_dotation", "primes_liees_reserve_capital",
            "ecarts_reevaluation", "benefices_non_distribue", "resultat_net_exercie",
            "created_by", "updated_by"
        ]

class GetLiabilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liabilities
        fields = '__all__'

class EditLiabilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liabilities
        fields = [
            "id", "annee", "acheteur", "tresorerie_ccp", "autres_etablissement_credit",
            "a_terme", "comptes_epargne_court_terme", "comptes_epargne_terme", "bons_caisse",
            "autres_dette_a_vue", "autres_dette_a_terme", "titres_creance_autres_dettes",
            "compte_dordre_divers", "provision_pour_risque_charge", "provision_reglementee",
            "emprunt_subordonne_tire_emis", "subventions_investissement", "fonds_affecte",
            "fonds_pour_risque_bancaire_generaux", "capital_ou_dotation", "primes_liees_reserve_capital",
            "ecarts_reevaluation", "benefices_non_distribue", "resultat_net_exercie",
            "created_by", "updated_by"
        ]









class OffBalanceSheetSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = OffBalanceSheet
        fields = '__all__'

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
            "id", "annee", "acheteur", "en_faveur_des_ets_credit", "en_faveur_clientele",
            "pour_compte_ets_credit", "pour_compte_clientele", "engagement_sur_titre",
            "recu_ets_credit", "recu_ets_credit2", "recu_clientele", "engagement_sur_titre2",
            "created_by", "updated_by"
        ]

class GetOffBalanceSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffBalanceSheet
        fields = '__all__'

class EditOffBalanceSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffBalanceSheet
        fields = [
            "id", "annee", "acheteur", "en_faveur_des_ets_credit", "en_faveur_clientele",
            "pour_compte_ets_credit", "pour_compte_clientele", "engagement_sur_titre",
            "recu_ets_credit", "recu_ets_credit2", "recu_clientele", "engagement_sur_titre2",
            "created_by", "updated_by"
        ]








class ExpensesSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = Expenses
        fields = '__all__'

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
            "id", "annee", "acheteur", "interet_charges_assimilee_dette_interbancaire",
            "interet_charge_assimilee_dette_clientele", "interet_charge_assimilee_titre_creance",
            "chargesc_compte_bloque_dactionnaire_emprunt_sub", "autres_interets_charges_assimilee",
            "charges_sur_op_credit_bail_assimile", "commissions", "charges_sur_titre_placement",
            "charges_sur_operation_change", "charges_sur_operation_hors_bilan", "frais_divers_exploitation_bancaire",
            "achat_marchandises", "stocks_vendus", "variations_stocks_marchanides", "frais_personnel",
            "autres_frais_generaux", "dotations_amortissement_provision_immobilisation",
            "solde_perte_creance_hors_bilan", "excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux",
            "charges_exceptionnelle", "pertes_exercice_anterieurs", "impot_sur_revenu", "total_charges",
            "created_by", "updated_by"
        ]

class GetExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = '__all__'

class EditExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = [
            "id", "annee", "acheteur", "interet_charges_assimilee_dette_interbancaire",
            "interet_charge_assimilee_dette_clientele", "interet_charge_assimilee_titre_creance",
            "chargesc_compte_bloque_dactionnaire_emprunt_sub", "autres_interets_charges_assimilee",
            "charges_sur_op_credit_bail_assimile", "commissions", "charges_sur_titre_placement",
            "charges_sur_operation_change", "charges_sur_operation_hors_bilan", "frais_divers_exploitation_bancaire",
            "achat_marchandises", "stocks_vendus", "variations_stocks_marchanides", "frais_personnel",
            "autres_frais_generaux", "dotations_amortissement_provision_immobilisation",
            "solde_perte_creance_hors_bilan", "excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux",
            "charges_exceptionnelle", "pertes_exercice_anterieurs", "impot_sur_revenu", "total_charges",
            "created_by", "updated_by"
        ]











class ProductsSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = CustomUserSerializer()
    updated_by = CustomUserSerializer()

    class Meta:
        model = Products
        fields = '__all__'

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
            "id", "annee", "acheteur", "interets_produit_assimile_sur_pret_avance_interbancaire",
            "ineterets_produit_assimile_pret_avance_clientele", "interet_produit_sur_titre_dinvestissement",
            "revenu_gains_titre_pret_titre_subordonne", "autres_interets_produits_assimiles",
            "produits_leansing_operation_connexes", "commissions", "revenus_titre_negociable",
            "dividendes_produits_assimiles", "revenus_operation_de_change", "produits_opeations_hors_bilan",
            "produits_bancaire_divers", "marges_vente", "ventes_marchandises", "variation_stocks_marchandises",
            "produit_dexploitation_generale", "reprise_damortissement_provisions_sur_immobilisation",
            "solde_resultat_correction_valeur_sur_creance_hors_bilan",
            "excedent_reprise_fonds_pour_risque_bancaire_generaux", "produits_exceptionnels",
            "benefice_sur_exercice_anterieur", "perte", "created_by", "updated_by"
        ]

class GetProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = '__all__'

class EditProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = [
            "id", "annee", "acheteur", "interets_produit_assimile_sur_pret_avance_interbancaire",
            "ineterets_produit_assimile_pret_avance_clientele", "interet_produit_sur_titre_dinvestissement",
            "revenu_gains_titre_pret_titre_subordonne", "autres_interets_produits_assimiles",
            "produits_leansing_operation_connexes", "commissions", "revenus_titre_negociable",
            "dividendes_produits_assimiles", "revenus_operation_de_change", "produits_opeations_hors_bilan",
            "produits_bancaire_divers", "marges_vente", "ventes_marchandises", "variation_stocks_marchandises",
            "produit_dexploitation_generale", "reprise_damortissement_provisions_sur_immobilisation",
            "solde_resultat_correction_valeur_sur_creance_hors_bilan",
            "excedent_reprise_fonds_pour_risque_bancaire_generaux", "produits_exceptionnels",
            "benefice_sur_exercice_anterieur", "perte", "created_by", "updated_by"
        ]










class CommandeSerializer(serializers.ModelSerializer):
    client = CustomUserSerializer()
    acheteur = AcheteurSerializer()
    ville = VilleSerializer()
    ref_type_rapport = ModeleRapportSerializer()
    devise_credit_demande = DeviseSerializer()
    devise_credit_recommande = DeviseSerializer()

    class Meta:
        model = Commande
        fields = '__all__'

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
            "id", "notre_ref", "reference_client", "date_recept_commande", "date_rapport",
            "delais", "priorite", "raison_sociale", "type_rapport", "ref_type_rapport",
            "credit_demande", "devise_credit_demande", "credit_recommande", "devise_credit_recommande",
            "numero_adresse", "rue_adresse", "code_postale_adresse", "telephone", "email",
            "ville", "client", "acheteur", "status"
        ]

class GetCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = '__all__'

class CheckCommandeSerializer(serializers.ModelSerializer):
    client = CustomUserSerializer()
    acheteur = AcheteurSerializer()
    ville = VilleSerializer()
    ref_type_rapport = ModeleRapportSerializer()
    devise_credit_demande = DeviseSerializer()
    devise_credit_recommande = DeviseSerializer()
    class Meta:
        model = Commande
        fields = '__all__'

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
            "id", "notre_ref", "reference_client", "date_recept_commande", "date_rapport",
            "delais", "priorite", "raison_sociale", "type_rapport", "ref_type_rapport",
            "credit_demande", "devise_credit_demande", "credit_recommande", "devise_credit_recommande",
            "numero_adresse", "rue_adresse", "code_postale_adresse", "telephone", "email",
            "ville", "client", "acheteur", "status"
        ]










class AlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = '__all__'

class AddAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = ['reference', 'objet', 'content']

class EditAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = ['reference', 'objet', 'content']

class DocumentAlerteSerializer(serializers.ModelSerializer):
    alerte = AlerteSerializer()

    class Meta:
        model = DocumentAlerte
        fields = '__all__'

class AddDocumentAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAlerte
        fields = ['alerte', 'titre', 'fichier']

class EditDocumentAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAlerte
        fields = ['alerte', 'titre', 'fichier']











class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

class AddClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id", "nom", "email", "telephone", "adresse",
            "date_inscription", "actif"
        ]

class GetClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

class CheckClientSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Client
        fields = '__all__'

class EditClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id", "nom", "email", "telephone", "adresse",
            "date_inscription", "actif"
        ]
        
        
        
        
        
        
        
        
        
        
        

class PortefeuilleSerializer(serializers.ModelSerializer):
    client = ClientSerializer()

    class Meta:
        model = Portefeuille
        fields = '__all__'
        

class AddPortefeuilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portefeuille
        fields = [
            "id", "client", "nom", "created_at", "updated_at"
        ]
        
        
class AddPortefeuilleWithAcheteursSerializer(serializers.ModelSerializer):
    acheteurs = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Portefeuille
        fields = ['client', 'nom', 'acheteurs']

    def create(self, validated_data):
        acheteurs_data = validated_data.pop('acheteurs')
        portefeuille = Portefeuille.objects.create(**validated_data)

        for acheteur_id in acheteurs_data:
            PortefeuilleClient.objects.create(portefeuille=portefeuille, acheteur_id=acheteur_id)

        return portefeuille



class GetPortefeuilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portefeuille
        fields = '__all__'


class CheckPortefeuilleSerializer(serializers.ModelSerializer):
    client = ClientSerializer()  # Assurez-vous d'avoir un ClientSerializer défini

    class Meta:
        model = Portefeuille
        fields = '__all__'



class EditPortefeuilleSerializer(serializers.ModelSerializer):
    acheteurs = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Portefeuille
        fields = [
            "id", "client", "nom", "created_at", "updated_at", "acheteurs"
        ]















class PortefeuilleClientSerializer(serializers.ModelSerializer):
    portefeuille = PortefeuilleSerializer()
    acheteur = AcheteurSerializer()  # Assurez-vous d'avoir un AcheteurSerializer défini

    class Meta:
        model = PortefeuilleClient
        fields = '__all__'



class AddPortefeuilleClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortefeuilleClient
        fields = [
            "id", "portefeuille", "acheteur", "categorie"
        ]




class GetPortefeuilleClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortefeuilleClient
        fields = '__all__'




class CheckPortefeuilleClientSerializer(serializers.ModelSerializer):
    portefeuille = PortefeuilleSerializer()
    acheteur = AcheteurSerializer()  # Assurez-vous d'avoir un AcheteurSerializer défini

    class Meta:
        model = PortefeuilleClient
        fields = '__all__'










class CompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = '__all__'

class AddCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = [
            "id", "nom", "type_compte", "sous_type"
        ]

class GetCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = '__all__'

class CheckCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = '__all__'

class EditCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = [
            "id", "nom", "type_compte", "sous_type"
        ]








class ValeurCompteIrfsSerializer(serializers.ModelSerializer):
    
    compte = CompteFinancierIrfsSerializer()
    devise = DeviseSerializer()
    annee = AnneeSerializer()
    
    class Meta:
        model = ValeurCompteIrfs
        fields = '__all__'

class AddValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = [
            "id", "acheteur", "compte", "annee", "valeur", "devise"
        ]

class GetValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = '__all__'

class CheckValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = '__all__'

class EditValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = [
            "id", "acheteur", "compte", "annee", "valeur", "devise"
        ]










class RatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = '__all__'

class AddRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = [
            "id", "type_ratio", "nom", "formule"
        ]

class GetRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = '__all__'

class CheckRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = '__all__'

class EditRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = [
            "id", "type_ratio", "nom", "formule"
        ]












class ValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = '__all__'

class AddValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = [
            "id", "acheteur", "ratio", "annee", "valeur"
        ]

class GetValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = '__all__'

class CheckValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = '__all__'

class EditValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = [
            "id", "acheteur", "ratio", "annee", "valeur"
        ]
