from datetime import datetime
from decimal import Decimal
from pathlib import Path
import re

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from main.models import (
    Acheteur,
    Banquier,
    Commande,
    Devise,
    DonneesEnregistrement,
    Pays,
    Province,
    Resume,
    User,
    Ville,
)


def _normalize_space(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()


def _extract_first(pattern, text, flags=0, group=1, default=""):
    match = re.search(pattern, text, flags)
    if not match:
        return default
    return _normalize_space(match.group(group))


def _safe_email(value):
    if not value:
        return ""
    return _normalize_space(value).replace(",", ".").replace(";", ".").replace(" ", "").lower()


def _extract_pdf_payload(pdf_path):
    payload = {
        "raison_sociale": "AFRICAN DISTRIBUTION COMPANY",
        "liasse_ref": "LIAS3251226015553",
        "ncc": "0517069C",
        "rccm": "ABJ-2005-B-1733",
        "activite": "Commerce general de produits importes",
        "adresse_additional": "ADJAME 2-BIA",
        "boite_postale": "05 BP 3354 ABJ 05",
        "code_postal": "05BP3354",
        "ville": "Abidjan",
        "telephone": "+2250707058003",
        "email": "adc@adc.ci",
        "date_reception": datetime.strptime("26/12/2025", "%d/%m/%Y").date(),
        "provider": "DGI - GUDEF",
    }
    if not pdf_path:
        return payload
    path = Path(pdf_path)
    if not path.exists() or not path.is_file():
        return payload
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:12])
        compact = _normalize_space(text)
        if compact:
            payload["raison_sociale"] = _extract_first(
                r"Etats financiers.*?normal\s+\d{4}\s+([A-Z0-9' .\-&]+?)\s+\d{7}[A-Z]",
                compact,
                flags=re.IGNORECASE,
                default=payload["raison_sociale"],
            )
            payload["liasse_ref"] = _extract_first(r"\b(LIAS[0-9A-Z]+)\b", compact, default=payload["liasse_ref"])
            payload["ncc"] = _extract_first(r"\b(\d{7}[A-Z])\b", compact, default=payload["ncc"])
            payload["rccm"] = _extract_first(r"\b([A-Z]{2,4}-\d{4}-[A-Z]-\d+)\b", compact, default=payload["rccm"])
            payload["email"] = _safe_email(
                _extract_first(
                    r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.,-]+\.[A-Za-z]{2,})",
                    compact,
                    default=payload["email"],
                )
            )
            payload["telephone"] = _extract_first(
                r"(\+\(?225\)?[\s\-]?\d{8,12})",
                compact,
                default=payload["telephone"],
            )
            payload["code_postal"] = _extract_first(
                r"(\d{2}\s*BP\s*\d+)",
                compact,
                flags=re.IGNORECASE,
                default=payload["code_postal"],
            )
    except Exception:
        pass
    return payload


class Command(BaseCommand):
    help = (
        "Genere un dossier solvabilite Cote d'Ivoire (ADC) en reutilisant le seed complet "
        "et en enrichissant depuis le PDF fiscal."
    )

    def add_arguments(self, parser):
        parser.add_argument("--code", type=str, default="CIV-SOLV-TEST", help="Code acheteur.")
        parser.add_argument("--nom", type=str, default="African Distribution Company", help="Nom acheteur.")
        parser.add_argument(
            "--pdf",
            type=str,
            default=r"c:\Users\24174\Documents\projets\documents projets\ACREMAC\DONNEES DE TESTS\BILAN FISCAL 2024. ADC.pdf",
            help="Chemin PDF source.",
        )
        parser.add_argument("--years", type=str, default="2025,2024,2023,2022", help="Annees CSV.")
        parser.add_argument("--with-commande", action="store_true", help="Creer/mettre a jour la commande.")
        parser.add_argument("--force-reset", action="store_true", help="Purger puis regenerer le dossier acheteur.")

    def handle(self, *args, **options):
        code = options["code"].strip()
        nom = options["nom"].strip()
        payload = _extract_pdf_payload(options.get("pdf"))

        with transaction.atomic():
            call_command(
                "seed_solvabilite_gabon",
                code=code,
                nom=nom,
                years=options["years"],
                with_commande=options["with_commande"],
                force_reset=options["force_reset"],
            )

            acheteur = Acheteur.objects.filter(code=code).first()
            if not acheteur:
                raise CommandError(f"Acheteur introuvable apres seed: {code}")

            pays = (
                Pays.objects.filter(code__in=["CI", "CIV"]).first()
                or Pays.objects.filter(nom__icontains="ivoire").first()
                or Pays.objects.filter(nom__icontains="cote d'ivoire").first()
                or Pays.objects.filter(nom__icontains="cote ivoire").first()
            )
            if not pays:
                pays = Pays.objects.create(nom="Cote d'Ivoire", code="CI", afficher_au_dashboard=True)
            if not pays.afficher_au_dashboard:
                pays.afficher_au_dashboard = True
                pays.save(update_fields=["afficher_au_dashboard"])

            province = Province.objects.filter(pays=pays, nom__iexact="Abidjan").first() or Province.objects.filter(pays=pays).first()
            if not province:
                province = Province.objects.create(nom="Abidjan", code="ABJ", pays=pays)

            ville_name = (payload.get("ville") or "Abidjan").title()
            ville = Ville.objects.filter(pays=pays, nom__iexact=ville_name).first() or Ville.objects.filter(pays=pays).first()
            if not ville:
                ville = Ville.objects.create(nom=ville_name, code="ABJ", pays=pays, province=province)

            client_user = (
                User.objects.filter(is_client=True, is_active=True, pays=pays).order_by("id").first()
                or User.objects.filter(is_client=True, is_active=True).order_by("id").first()
            )
            if not client_user:
                raise CommandError("Aucun user client actif (is_client=True) trouve pour rattacher la commande.")

            devise_xof, _ = Devise.objects.get_or_create(code="XOF", defaults={"nom": "Franc CFA BCEAO", "symbole": "F CFA"})

            acheteur.nom = nom
            acheteur.sigle = "ADC"
            acheteur.activite_principale = payload.get("activite") or acheteur.activite_principale
            acheteur.email = (payload.get("email") or acheteur.email or "adc@adc.ci")[:254]
            acheteur.site_internet = acheteur.site_internet or "https://www.adc.ci"
            acheteur.numero_adresse = acheteur.numero_adresse or "12"
            acheteur.rue_adresse = (payload.get("adresse_additional") or acheteur.rue_adresse or "ADJAME 2-BIA")[:200]
            acheteur.code_postal = (payload.get("code_postal") or acheteur.code_postal or "05BP3354")[:200]
            acheteur.boite_postale = (payload.get("boite_postale") or acheteur.boite_postale or "05 BP 3354 ABJ 05")[:200]
            acheteur.fax = acheteur.fax or "+22521245396"
            acheteur.pays = pays
            acheteur.province = province
            acheteur.ville = ville
            acheteur.commentaire = "Dossier Cote d'Ivoire genere depuis PDF fiscal ADC."
            acheteur.save()

            Resume.objects.filter(acheteur=acheteur).update(devise=devise_xof)
            DonneesEnregistrement.objects.filter(acheteur=acheteur).update(
                numero_registre_commerce=(payload.get("rccm") or "ABJ-2005-B-1733")[:50],
                numero_fiscale=(payload.get("ncc") or "0517069C")[:50],
            )
            Banquier.objects.filter(acheteur=acheteur).update(ville=ville, code_postal="ABJ-01")

            if options["with_commande"]:
                ref_client = payload.get("liasse_ref") or f"CMD-{code}"
                commande, _ = Commande.objects.update_or_create(
                    acheteur=acheteur,
                    reference_client=ref_client,
                    defaults={
                        "notre_ref": f"ACR-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                        "raison_sociale": (payload.get("raison_sociale") or nom)[:100],
                        "type_rapport": "--------",
                        "date_recept_commande": payload.get("date_reception") or timezone.localdate(),
                        "date_rapport": timezone.localdate(),
                        "delais": "10 jours",
                        "priorite": "Normale",
                        "credit_demande": Decimal("650000000"),
                        "credit_recommande": Decimal("520000000"),
                        "devise_credit_demande": devise_xof,
                        "devise_credit_recommande": devise_xof,
                        "numero_adresse": acheteur.numero_adresse or "12",
                        "rue_adresse": (payload.get("adresse_additional") or acheteur.rue_adresse or "ADJAME 2-BIA")[:200],
                        "code_postale_adresse": (payload.get("code_postal") or acheteur.code_postal or "05BP3354")[:200],
                        "telephone": (payload.get("telephone") or "+2250707058003")[:100],
                        "email": (payload.get("email") or acheteur.email or "adc@adc.ci")[:100],
                        "pays": pays,
                        "ville": ville,
                        "client": client_user,
                        "status": "nouvelle",
                        "type_commande": "NORMALE",
                        "type_traitement": "MANUEL",
                        "client_nom": (client_user.get_username() or "")[:255],
                        "company_identification_number": (payload.get("rccm") or "")[:100],
                        "address_additional": (payload.get("adresse_additional") or "")[:100],
                        "state": ville_name[:100],
                        "postcode": (payload.get("code_postal") or "")[:100],
                        "post_office": (payload.get("boite_postale") or "")[:100],
                        "provider": (payload.get("provider") or "DGI - GUDEF")[:100],
                        "comments": (f"Seed CI depuis PDF fiscal. NCC={payload.get('ncc')} RCCM={payload.get('rccm')}")[:100],
                    },
                )
                self.stdout.write(f"Commande ID: {commande.id} | ref_client: {commande.reference_client}")

        self.stdout.write(self.style.SUCCESS("Seed solvabilite Cote d'Ivoire termine."))
        self.stdout.write(f"Acheteur code={code} | nom={nom}")
        self.stdout.write(f"LIASSE: {payload.get('liasse_ref')}")
