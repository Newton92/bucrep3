# forms.py
from django import forms

from main.models import *
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from safedelete.models import HARD_DELETE


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'telephone', 'address', 'profession', 'email_cc',
            'role', 'pays', 'activation', 'auth_a2f',
            'is_active', 'is_staff', 'is_client',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ces champs sont auto-gérés par Django ; l'admin les injecte dans le
        # formulaire combiné mais ils ne doivent pas bloquer la validation.
        for fname in ('password', 'date_joined', 'last_login', 'password_changed_at'):
            if fname in self.fields:
                self.fields[fname].required = False


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ IMPORTANT AVEC SAFEDELETE
        self.fields['pays'].queryset = Pays.all_objects.filter(is_active=True)



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
