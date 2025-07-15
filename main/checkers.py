# surveillance/checkers.py

from main.models import AlerteLog, ResponsableAcheteur


def check_executive_change(portefeuille, acheteur, element_surveille, last_check_date):
    """
    Vérifie si de nouveaux dirigeants ont été ajoutés ou mis à jour
    pour un acheteur depuis la dernière vérification.
    """
    # Si last_check_date est None (première vérification), on ne fait rien pour éviter de tout remonter.
    if not last_check_date:
        return

    # On cherche les responsables créés OU mis à jour depuis la dernière vérification
    nouveaux_dirigeants = ResponsableAcheteur.objects.filter(
        acheteur=acheteur, updated_at__gt=last_check_date
    )

    for dirigeant in nouveaux_dirigeants:
        message = f"Mouvement de dirigeant détecté : {dirigeant.prenom} {dirigeant.nom}, poste : {dirigeant.poste}."

        # On crée une alerte en base de données
        AlerteLog.objects.create(
            portefeuille=portefeuille,
            acheteur=acheteur,
            element_surveille=element_surveille,
            message=message,
            content_object=dirigeant,  # On lie l'alerte à l'objet dirigeant spécifique
        )
        print(f"ALERTE CRÉÉE : {message}")  # Pour le debug


# On peut en créer un autre pour la mise à jour de l'acheteur lui-même
def check_contact_info_change(
    portefeuille, acheteur, element_surveille, last_check_date
):
    """
    Vérifie si la fiche de l'acheteur (adresse, etc.) a été mise à jour.
    """
    if not last_check_date:
        return

    # On vérifie simplement si l'objet Acheteur a été mis à jour
    if acheteur.updated_at > last_check_date:
        message = f"La fiche de l'entreprise '{acheteur.nom}' a été mise à jour (adresse, contact...)."
        AlerteLog.objects.create(
            portefeuille=portefeuille,
            acheteur=acheteur,
            element_surveille=element_surveille,
            message=message,
            content_object=acheteur,
        )
        print(f"ALERTE CRÉÉE : {message}")


# REGISTRY : Le dictionnaire qui fait le lien entre code et fonction
CHECKER_REGISTRY = {
    "EXECUTIVE_CHANGE": check_executive_change,
    "CONTACT_INFO_CHANGE": check_contact_info_change,
    # Ajoutez ici les autres codes et leurs fonctions de vérification
    # "COMPANY_NAME_CHANGE": check_company_name_change,
}


# surveillance/checkers.py

from .models import AlerteLog, ResponsableAcheteur

# ... fonctions existantes (check_executive_change, etc.) ...


def check_dissolution(portefeuille, acheteur, element_surveille, last_check_date):
    """
    Vérifie si le statut de l'entreprise est passé à "Dissoute" ou "Liquidée".
    Hypothèse: le statut est un champ texte ou une clé étrangère sur le modèle Acheteur.
    """
    if not last_check_date:
        return

    # On vérifie si l'acheteur a été mis à jour ET si son statut est pertinent
    # Adaptez `statut_entreprise.nom` au nom de votre champ réel.
    statuts_critiques = ["Dissolution", "Liquidation", "Dissoute", "Liquidée"]

    if (
        acheteur.updated_at > last_check_date
        and acheteur.statut_entreprise
        and acheteur.statut_entreprise.nom in statuts_critiques
    ):
        message = f"L'entreprise '{acheteur.nom}' a un nouveau statut critique : {acheteur.statut_entreprise.nom}."
        AlerteLog.objects.create(
            portefeuille=portefeuille,
            acheteur=acheteur,
            element_surveille=element_surveille,
            message=message,
            content_object=acheteur,
        )
        print(f"ALERTE CRÉÉE : {message}")


def check_company_name_change(
    portefeuille, acheteur, element_surveille, last_check_date
):
    """
    Détecte un changement de raison sociale.
    Note : Cette vérification est basique et se déclenche sur toute mise à jour de la fiche Acheteur.
    Pour savoir si *seulement* le nom a changé, il faudrait un système de logging plus complexe.
    """
    if not last_check_date:
        return

    # On vérifie si l'objet Acheteur a été mis à jour.
    # On se base sur le fait qu'un changement de raison sociale entrainera une mise à jour.
    if acheteur.updated_at > last_check_date:
        message = f"Une mise à jour de la fiche de '{acheteur.nom}' a été détectée, pouvant indiquer un changement de raison sociale."
        AlerteLog.objects.create(
            portefeuille=portefeuille,
            acheteur=acheteur,
            element_surveille=element_surveille,
            message=message,
            content_object=acheteur,
        )
        print(f"ALERTE CRÉÉE : {message}")


# --- Le REGISTRY mis à jour ---
CHECKER_REGISTRY = {
    "EXECUTIVE_CHANGE": check_executive_change,
    "CONTACT_INFO_CHANGE": check_contact_info_change,
    "COMPANY_NAME_CHANGE": check_company_name_change,
    "DISSOLUTION": check_dissolution,
    "LIQUIDATION": check_dissolution,  # On peut réutiliser la même fonction
    # Ajoutez ici les autres :
    # "NEW_FINANCIALS": votre_fonction_pour_les_finances,
    # ... etc
}
