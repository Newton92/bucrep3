import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class PasswordValidator:
    """
    Validateur personnalisé pour les mots de passe
    """
    
    def validate(self, password, user=None):
        errors = []
        
        # Vérifier la longueur minimale
        if len(password) < 8:
            errors.append(
                _("Le mot de passe doit contenir au moins 8 caractères.")
            )
        
        # Vérifier la présence d'une majuscule
        if not re.search(r'[A-Z]', password):
            errors.append(
                _("Le mot de passe doit contenir au moins une lettre majuscule.")
            )
        
        # Vérifier la présence d'une minuscule
        if not re.search(r'[a-z]', password):
            errors.append(
                _("Le mot de passe doit contenir au moins une lettre minuscule.")
            )
        
        # Vérifier la présence d'un chiffre
        if not re.search(r'[0-9]', password):
            errors.append(
                _("Le mot de passe doit contenir au moins un chiffre.")
            )
        
        # Vérifier la présence d'un caractère spécial
        if not re.search(r'[@$!%*?&]', password):
            errors.append(
                _("Le mot de passe doit contenir au moins un caractère spécial (@$!%*?&).")
            )
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            "Votre mot de passe doit contenir au moins :\n"
            "- 8 caractères\n"
            "- Une lettre majuscule\n"
            "- Une lettre minuscule\n"
            "- Un chiffre\n"
            "- Un caractère spécial (@$!%*?&)"
        )
        
        
        
        
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class PasswordStrengthValidator:
    """
    Validateur de force du mot de passe pour Django
    """
    
    def validate(self, password, user=None):
        errors = []
        
        # Longueur minimale
        if len(password) < 8:
            errors.append(_("Le mot de passe doit contenir au moins 8 caractères."))
        
        # Majuscule
        if not re.search(r'[A-Z]', password):
            errors.append(_("Le mot de passe doit contenir au moins une lettre majuscule."))
        
        # Minuscule
        if not re.search(r'[a-z]', password):
            errors.append(_("Le mot de passe doit contenir au moins une lettre minuscule."))
        
        # Chiffre
        if not re.search(r'[0-9]', password):
            errors.append(_("Le mot de passe doit contenir au moins un chiffre."))
        
        # Caractère spécial
        if not re.search(r'[@$!%*?&]', password):
            errors.append(_("Le mot de passe doit contenir au moins un caractère spécial (@$!%*?&)."))
        
        # Mots de passe courants
        common_passwords = [
            'password', '12345678', 'qwerty', 'azerty', 
            'admin123', 'bucrep2025', 'bucrep', 'acremac'
        ]
        if password.lower() in common_passwords:
            errors.append(_("Ce mot de passe est trop commun. Veuillez en choisir un autre."))
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            "Votre mot de passe doit contenir au moins :\n"
            "- 8 caractères\n"
            "- Une lettre majuscule\n"
            "- Une lettre minuscule\n"
            "- Un chiffre\n"
            "- Un caractère spécial (@$!%*?&)\n"
            "- Ne pas être un mot de passe courant"
        )