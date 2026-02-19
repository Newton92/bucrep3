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
        "raison_sociale": "Aquatan Proprietary Limited",
        "registration_no": "1990/005957/07",
        "activite": "Supply and installation of geosynthetic materials",
        "adresse_additional": "8 Nuwejaarsvoel Avenue, Birch Acres Extension 7",
        "boite_postale": "PO Box 633, Isando, 1600",
        "code_postal": "1618",
        "ville": "Kempton Park",
        "province": "Gauteng",
        "telephone": "+27110000000",
        "email": "info@aquatan.co.za",
        "date_reception": datetime.strptime("09/07/2025", "%d/%m/%Y").date(),
        "provider": "AFS Signed",
        "country_name": "South Africa",
        "country_code": "ZA",
        "profit_2024": "6216370",
        "profit_2023": "13692250",
        "tax_2024": "2879861",
        "tax_2023": "1315854",
        "issued_date_text": "09 July 2025",
    }
    if not pdf_path:
        return payload

    path = Path(pdf_path)
    if not path.exists() or not path.is_file():
        return payload

    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:14])
        compact = _normalize_space(text)
        if not compact:
            return payload

        payload["raison_sociale"] = _extract_first(
            r"(Aquatan Proprietary Limited)",
            compact,
            flags=re.IGNORECASE,
            default=payload["raison_sociale"],
        )
        payload["registration_no"] = _extract_first(
            r"Registration number[:\)\s]*([0-9]{4}/[0-9]{6}/[0-9]{2})",
            compact,
            flags=re.IGNORECASE,
            default=payload["registration_no"],
        )
        payload["activite"] = _extract_first(
            r"Nature of business and principal activities\s+(.+?)\s+Directors",
            compact,
            flags=re.IGNORECASE,
            default=payload["activite"],
        )
        payload["adresse_additional"] = _extract_first(
            r"Registered office and business address\s+(.+?)\s+Postal address",
            compact,
            flags=re.IGNORECASE,
            default=payload["adresse_additional"],
        )
        payload["boite_postale"] = _extract_first(
            r"Postal address\s+(.+?)\s+Holding company",
            compact,
            flags=re.IGNORECASE,
            default=payload["boite_postale"],
        )
        payload["ville"] = _extract_first(
            r"Registered office and business address.+?\s(Kempton Park)\s",
            compact,
            flags=re.IGNORECASE,
            default=payload["ville"],
        ).title()
        payload["province"] = _extract_first(
            r"Registered office and business address.+?\s(Gauteng)\s+1618",
            compact,
            flags=re.IGNORECASE,
            default=payload["province"],
        ).title()
        payload["code_postal"] = _extract_first(
            r"Registered office and business address.+?\s(Gauteng)\s+([0-9]{4})",
            compact,
            flags=re.IGNORECASE,
            group=2,
            default=payload["code_postal"],
        )
        payload["country_name"] = _extract_first(
            r"Country of incorporation and domicile\s+(South Africa)",
            compact,
            flags=re.IGNORECASE,
            default=payload["country_name"],
        ).title()
        payload["issued_date_text"] = _extract_first(
            r"\b((?:0[1-9]|[12][0-9]|3[01])\s+[A-Za-z]+\s+20[0-9]{2})\b",
            compact,
            flags=re.IGNORECASE,
            default=payload["issued_date_text"],
        )

        profit = _extract_first(
            r"total comprehensive profit.+?2024.*?R\s*([0-9\s]+)\s*\(.*?2023:\s*R\s*([0-9\s]+)\)",
            compact,
            flags=re.IGNORECASE,
            group=1,
        )
        profit_prev = _extract_first(
            r"total comprehensive profit.+?2024.*?R\s*([0-9\s]+)\s*\(.*?2023:\s*R\s*([0-9\s]+)\)",
            compact,
            flags=re.IGNORECASE,
            group=2,
        )
        tax = _extract_first(
            r"taxation expense of R\s*([0-9\s]+)\s*\(2023:\s*R\s*([0-9\s]+)\)",
            compact,
            flags=re.IGNORECASE,
            group=1,
        )
        tax_prev = _extract_first(
            r"taxation expense of R\s*([0-9\s]+)\s*\(2023:\s*R\s*([0-9\s]+)\)",
            compact,
            flags=re.IGNORECASE,
            group=2,
        )
        if profit:
            payload["profit_2024"] = re.sub(r"\s+", "", profit)
        if profit_prev:
            payload["profit_2023"] = re.sub(r"\s+", "", profit_prev)
        if tax:
            payload["tax_2024"] = re.sub(r"\s+", "", tax)
        if tax_prev:
            payload["tax_2023"] = re.sub(r"\s+", "", tax_prev)

    except Exception:
        pass

    return payload


class Command(BaseCommand):
    help = (
        "Genere un dossier solvabilite South Africa (Aquatan Proprietary Limited) "
        "en se basant sur le PDF AFS et en generant les donnees complementaires."
    )

    def add_arguments(self, parser):
        parser.add_argument("--code", type=str, default="ZA-SOLV-TEST", help="Code acheteur.")
        parser.add_argument("--nom", type=str, default="Aquatan Proprietary Limited", help="Nom acheteur.")
        parser.add_argument(
            "--pdf",
            type=str,
            default=r"c:\Users\24174\Documents\projets\documents projets\ACREMAC\DONNEES DE TESTS\Aquatan Proprietary Limited 2024 - Signed AFS.pdf",
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
                Pays.objects.filter(code__in=["ZA", "ZAF"]).first()
                or Pays.objects.filter(nom__icontains="south africa").first()
                or Pays.objects.filter(nom__icontains="afrique du sud").first()
            )
            if not pays:
                pays = Pays.objects.create(nom="South Africa", code="ZA", afficher_au_dashboard=True)
            if not pays.afficher_au_dashboard:
                pays.afficher_au_dashboard = True
                pays.save(update_fields=["afficher_au_dashboard"])

            province_name = payload.get("province") or "Gauteng"
            province = Province.objects.filter(pays=pays, nom__iexact=province_name).first() or Province.objects.filter(pays=pays).first()
            if not province:
                province = Province.objects.create(nom=province_name, code="GT", pays=pays)

            ville_name = (payload.get("ville") or "Kempton Park").title()
            ville = Ville.objects.filter(pays=pays, nom__iexact=ville_name).first()
            if not ville:
                ville = Ville.objects.create(nom=ville_name, code="KEMPTON", pays=pays, province=province)

            client_user = (
                User.objects.filter(is_client=True, is_active=True, pays=pays).order_by("id").first()
                or User.objects.filter(is_client=True, is_active=True).order_by("id").first()
            )
            if not client_user:
                raise CommandError("Aucun user client actif (is_client=True) trouve pour rattacher la commande.")

            devise_zar, _ = Devise.objects.get_or_create(code="ZAR", defaults={"nom": "South African Rand", "symbole": "R"})

            acheteur.nom = nom
            acheteur.sigle = "AQUATAN"
            acheteur.activite_principale = payload.get("activite") or acheteur.activite_principale
            acheteur.email = (payload.get("email") or acheteur.email or "info@aquatan.co.za")[:254]
            acheteur.site_internet = acheteur.site_internet or "https://www.aquatan.com"
            acheteur.numero_adresse = "8"
            acheteur.rue_adresse = (payload.get("adresse_additional") or acheteur.rue_adresse or "Nuwejaarsvoel Avenue")[:200]
            acheteur.code_postal = (payload.get("code_postal") or acheteur.code_postal or "1618")[:200]
            acheteur.boite_postale = (payload.get("boite_postale") or acheteur.boite_postale or "PO Box 633, Isando, 1600")[:200]
            acheteur.fax = acheteur.fax or "+27110000001"
            acheteur.pays = pays
            acheteur.province = province
            acheteur.ville = ville
            acheteur.commentaire = "Dossier South Africa genere depuis PDF AFS Aquatan."
            acheteur.save()

            Resume.objects.filter(acheteur=acheteur).update(
                devise=devise_zar,
                chiffre_affaire=Decimal("125000000"),
                resultat_net=Decimal(payload.get("profit_2024") or "6216370"),
                commentaire=f"AFS 2024: profit net R {payload.get('profit_2024')} (2023: R {payload.get('profit_2023')}).",
            )
            DonneesEnregistrement.objects.filter(acheteur=acheteur).update(
                numero_registre_commerce=(payload.get("registration_no") or "1990/005957/07")[:50],
                numero_fiscale=(payload.get("registration_no") or "1990/005957/07")[:50],
            )
            Banquier.objects.filter(acheteur=acheteur).update(ville=ville, code_postal=(payload.get("code_postal") or "1618")[:20])

            if options["with_commande"]:
                ref_client = (payload.get("registration_no") or f"CMD-{code}").replace("/", "-")
                commande, _ = Commande.objects.update_or_create(
                    acheteur=acheteur,
                    reference_client=ref_client,
                    defaults={
                        "notre_ref": f"ACR-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                        "raison_sociale": (payload.get("raison_sociale") or nom)[:100],
                        "type_rapport": "--------",
                        "date_recept_commande": payload.get("date_reception") or timezone.localdate(),
                        "date_rapport": timezone.localdate(),
                        "delais": "14 days",
                        "priorite": "Normal",
                        "credit_demande": Decimal("12000000"),
                        "credit_recommande": Decimal("9500000"),
                        "devise_credit_demande": devise_zar,
                        "devise_credit_recommande": devise_zar,
                        "numero_adresse": acheteur.numero_adresse or "8",
                        "rue_adresse": (payload.get("adresse_additional") or acheteur.rue_adresse or "Nuwejaarsvoel Avenue")[:200],
                        "code_postale_adresse": (payload.get("code_postal") or acheteur.code_postal or "1618")[:200],
                        "telephone": (payload.get("telephone") or "+27110000000")[:100],
                        "email": (payload.get("email") or acheteur.email or "info@aquatan.co.za")[:100],
                        "pays": pays,
                        "ville": ville,
                        "client": client_user,
                        "status": "nouvelle",
                        "type_commande": "NORMALE",
                        "type_traitement": "MANUEL",
                        "client_nom": (client_user.get_username() or "")[:255],
                        "company_identification_number": (payload.get("registration_no") or "")[:100],
                        "address_additional": (payload.get("adresse_additional") or "")[:100],
                        "state": (province_name or "Gauteng")[:100],
                        "postcode": (payload.get("code_postal") or "1618")[:100],
                        "post_office": (payload.get("boite_postale") or "")[:100],
                        "provider": (payload.get("provider") or "AFS Signed")[:100],
                        "comments": (
                            f"Seed ZA depuis AFS. Reg={payload.get('registration_no')} Profit2024={payload.get('profit_2024')}"
                        )[:100],
                    },
                )
                self.stdout.write(f"Commande ID: {commande.id} | ref_client: {commande.reference_client}")

        self.stdout.write(self.style.SUCCESS("Seed solvabilite South Africa termine."))
        self.stdout.write(f"Acheteur code={code} | nom={nom}")
        self.stdout.write(f"Registration: {payload.get('registration_no')}")
        self.stdout.write(f"Issued: {payload.get('issued_date_text')}")
