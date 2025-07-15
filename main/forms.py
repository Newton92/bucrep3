# forms.py
from django import forms

from main.models import *


class PortefeuilleForm(forms.ModelForm):
    class Meta:
        model = Portefeuille
        fields = [
            "nom",
            "client",
            "elements_surveillance_actifs",
            "frequence_alertes",
        ]  # Ajoutez les autres champs nécessaires
        widgets = {
            "elements_surveillance_actifs": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optionnel : Ordonner les choix pour une meilleure lisibilité
        self.fields["elements_surveillance_actifs"].queryset = (
            ElementSurveillance.objects.order_by("categorie", "sous_categorie", "nom")
        )
