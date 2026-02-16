# serializers_reporting.py
from rest_framework import serializers
from main.models import Annee, Devise, Commande, Acheteur
from django.utils.translation import gettext_lazy as _

class AnneeSerializer(serializers.ModelSerializer):
    value = serializers.IntegerField(source='annee')
    label = serializers.SerializerMethodField()

    class Meta:
        model = Annee
        fields = ['value', 'label']

    def get_label(self, obj):
        return str(obj.annee)

class DeviseSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='code')
    label = serializers.SerializerMethodField()

    class Meta:
        model = Devise
        fields = ['value', 'label']

    def get_label(self, obj):
        return f"{obj.nom} ({obj.code})"


class CommandeSerializer(serializers.ModelSerializer):
    value = serializers.IntegerField(source='id')
    label = serializers.SerializerMethodField()
    date_creation_formatee = serializers.SerializerMethodField()

    class Meta:
        model = Commande
        fields = ['value', 'label', 'date_creation_formatee', 'notre_ref', 'raison_sociale', 'created_at']

    def get_label(self, obj):
        ref = obj.notre_ref or 'Sans référence'
        raison_sociale = (obj.raison_sociale or 'Sans raison sociale')[:25] + '...' if len(obj.raison_sociale or '') > 25 else (obj.raison_sociale or 'Sans raison sociale')
        
        # Formater la date avec heure et minutes
        if obj.created_at:
            date_formatee = obj.created_at.strftime("%d/%m/%Y %H:%M")
        else:
            date_formatee = "Date inconnue"
        
        return f"{ref} - {raison_sociale} - {date_formatee}"

    def get_date_creation_formatee(self, obj):
        return obj.created_at.strftime("%d/%m/%Y %H:%M") if obj.created_at else "Date inconnue"
    

class RapportSolvabiliteSerializer(serializers.Serializer):
    annee_n = serializers.IntegerField(required=True)
    annee_n1 = serializers.IntegerField(required=True)
    annee_n2 = serializers.IntegerField(required=True)
    inclure_commande = serializers.ChoiceField(
        choices=[('oui', 'Oui'), ('non', 'Non')],
        required=True
    )
    commande_id = serializers.IntegerField(required=False, allow_null=True)
    langue = serializers.ChoiceField(
        choices=[('fr', 'Français'), ('en', 'English')],
        required=True
    )
    devise = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    type_bilan = serializers.ChoiceField(
        choices=[
            ('classique', 'Classique'),
            ('bancaire', 'Bancaire'),
            ('anglais', 'Anglais'),
            ('syscohada', 'Syscohada'),
            ('ifrs', 'IFRS COBAC'),  # <-- Correction ici
            ('irfs_cobac', 'IFRS COBAC'),  # OU gardez cette valeur
        ],
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    format_rapport = serializers.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('html', 'HTML'),
            ('xml', 'XML'),
            ('json', 'JSON')
        ],
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    acheteur_id = serializers.IntegerField(required=True)  # <-- Ajoutez ou vérifiez cette ligne
    
    def validate_acheteur_id(self, value):
        if not Acheteur.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Acheteur non trouvé.")
        return value

    def validate(self, data):
        # Validation des années
        annees = [data['annee_n'], data['annee_n1'], data['annee_n2']]
        if len(set(annees)) != 3:
            raise serializers.ValidationError("Les années doivent être distinctes.")
        
        # Validation de la commande si inclure_commande est 'oui'
        if data.get('inclure_commande') == 'oui' and not data.get('commande_id'):
            raise serializers.ValidationError("Une commande doit être sélectionnée.")
        
        if data.get('inclure_commande') == 'non':
            data['commande_id'] = None

        # Prévisualisation: ces champs peuvent être omis et seront résolus côté vue.
        if not data.get('devise'):
            data['devise'] = None
        if not data.get('type_bilan'):
            data['type_bilan'] = None
        if not data.get('format_rapport'):
            data['format_rapport'] = None

        return data
