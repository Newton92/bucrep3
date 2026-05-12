from django import template

register = template.Library()

@register.filter
def get_stabilite_text(score):
    """Texte pour stabilité politique"""
    try:
        score_int = int(score)
        if score_int >= 8: return 'Très stable'
        elif score_int >= 6: return 'Stable'
        elif score_int >= 4: return 'Modérément stable'
        else: return 'Instable'
    except: return 'Non évalué'

@register.filter
def get_droit_text(score):
    """Texte pour état de droit"""
    try:
        score_int = int(score)
        if score_int >= 8: return 'Forte application de la loi'
        elif score_int >= 6: return 'Bon état de droit'
        elif score_int >= 4: return 'État de droit moyen'
        else: return 'Faible état de droit'
    except: return 'Non évalué'

@register.filter
def get_efficacite_text(score):
    """Texte pour efficacité gouvernementale"""
    try:
        score_int = int(score)
        if score_int >= 8: return 'Très efficace'
        elif score_int >= 6: return 'Efficace'
        elif score_int >= 4: return 'Modérément efficace'
        else: return 'Inefficace'
    except: return 'Non évalué'

@register.filter
def get_qualite_text(score):
    """Texte pour qualité réglementaire"""
    try:
        score_int = int(score)
        if score_int >= 8: return 'Excellente réglementation'
        elif score_int >= 6: return 'Bonne réglementation'
        elif score_int >= 4: return 'Réglementation moyenne'
        else: return 'Mauvaise réglementation'
    except: return 'Non évalué'

@register.filter
def get_liberte_text(score):
    """Texte pour liberté d'expression"""
    try:
        score_int = int(score)
        if score_int >= 8: return 'Très libre'
        elif score_int >= 6: return 'Libre'
        elif score_int >= 4: return 'Modérément libre'
        else: return 'Restrictive'
    except: return 'Non évalué'

@register.filter
def get_score_color(score):
    """Retourne la couleur CSS en fonction du score"""
    try:
        score_int = int(score)
        if score_int >= 8:
            return 'success'
        elif score_int >= 6:
            return 'warning'
        elif score_int >= 4:
            return 'danger'
        else:
            return 'danger'
    except (ValueError, TypeError):
        return 'danger'

@register.filter
def get_score_text(score, score_type):
    """Retourne le texte descriptif en fonction du score"""
    try:
        score_int = int(score)
        if score_int >= 8:
            texts = {
                'stabilite': 'Très stable',
                'droit': 'Forte application de la loi',
                'efficacite': 'Très efficace',
                'qualite': 'Excellente réglementation',
                'liberte': 'Très libre',
            }
        elif score_int >= 6:
            texts = {
                'stabilite': 'Stable',
                'droit': 'Bon état de droit',
                'efficacite': 'Efficace',
                'qualite': 'Bonne réglementation',
                'liberte': 'Libre',
            }
        elif score_int >= 4:
            texts = {
                'stabilite': 'Modérément stable',
                'droit': 'État de droit moyen',
                'efficacite': 'Modérément efficace',
                'qualite': 'Réglementation moyenne',
                'liberte': 'Modérément libre',
            }
        else:
            texts = {
                'stabilite': 'Instable',
                'droit': 'Faible état de droit',
                'efficacite': 'Inefficace',
                'qualite': 'Mauvaise réglementation',
                'liberte': 'Restrictive',
            }
        
        return texts.get(score_type, '')
    except (ValueError, TypeError):
        return 'Non évalué'