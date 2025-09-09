# main/templatetags/custom_filters.py

from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Permet d'accéder à un élément d'un dictionnaire par sa clé.
    Exemple: {{ my_dict|get_item:my_key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def floatformat(value, arg='-2'):
    """
    Affiche une valeur décimale avec le nombre de décimales spécifié.
    Gère les valeurs None et non numériques.
    """
    try:
        if value is None or not isinstance(value, (int, float, Decimal)):
            return "N/A"
        
        value = float(value)
        arg = int(arg)
        
        # Pour les nombres négatifs, on supprime le signe de l'argument
        if arg < 0:
            arg = -arg
        
        format_string = f'{{:.{arg}f}}'
        return format_string.format(value).replace('.', ',')
        
    except (ValueError, TypeError):
        return "N/A"