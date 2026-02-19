import re
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from main.models import (
    Acheteur,
    CategorieEntreprise,
    Commande,
    FormeJuridique,
    Pays,
    Province,
    StatutEntreprise,
    User,
    Ville,
)


def _normalize_space(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()


def _safe_email(value):
    if not value:
        return ""
    email = value.strip().replace(",", ".").replace(";", ".")
    email = re.sub(r"\s+", "", email)
    return email.lower()


def _extract_first(pattern, text, flags=0, group=1, default=""):
    match = re.search(pattern, text, flags)
    if not match:
        return default
    return _normalize_space(match.group(group))


def _clamp(value, length):
    if value is None:
        return ""
    return str(value)[:length]


def _parse_date_from_text(compact):
    candidate = _extract_first(r"Date de transmission\s*:?\s*(\d{2}/\d{2}/\d{4})", compact, flags=re.IGNORECASE)
    if not candidate:
        candidate = _extract_first(r"\b(\d{2}/\d{2}/\d{4})\b", compact)
    if not candidate:
        return None
    try:
        return datetime.strptime(candidate, "%d/%m/%Y").date()
    except ValueError:
        return None


def _extract_data_from_text(text):
    compact = _normalize_space(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    year = _extract_first(r"Etats financiers\s+syst[\w\u00E8\u00E9]+me\s+normal\s+(\d{4})", compact, flags=re.IGNORECASE)
    if not year:
        year = _extract_first(r"Etats financiers.*?normal\s+(\d{4})", compact, flags=re.IGNORECASE)

    liasse_ref = _extract_first(r"\b(LIAS[0-9A-Z]+)\b", compact)
    ncc = _extract_first(r"\b(\d{7}[A-Z])\b", compact)
    rccm = _extract_first(r"\b([A-Z]{2,4}-\d{4}-[A-Z]-\d+)\b", compact)

    phone = _extract_first(r"(\+\(?\d{1,3}\)?[\s\-]?\d{6,12})", compact)
    if not phone:
        phone = _extract_first(r"\b(2\d{7,9})\b", compact)

    email = _safe_email(_extract_first(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.,-]+\.[A-Za-z]{2,})", compact))
    provider = _extract_first(r"(DGI\s*-\s*GUDEF)", compact, flags=re.IGNORECASE, default="DGI - GUDEF")

    raison_sociale = ""
    for idx, line in enumerate(lines):
        if re.search(r"Etats financiers.*?normal\s+\d{4}", line, flags=re.IGNORECASE):
            if idx + 1 < len(lines):
                raison_sociale = _normalize_space(lines[idx + 1])
                break

    if not raison_sociale:
        raison_sociale = _extract_first(
            r"Etats financiers.*?normal\s+\d{4}\s+([A-Z0-9' .\-&]+?)\s+\d{7}[A-Z]",
            compact,
            flags=re.IGNORECASE,
        )
    if not raison_sociale and liasse_ref:
        raison_sociale = _extract_first(
            rf"Etats financiers.*?normal\s+\d{{4}}\s+(.+?)\s+\d{{7}}[A-Z].+?{re.escape(liasse_ref)}",
            compact,
            flags=re.IGNORECASE,
        )

    activite = ""
    if ncc:
        activite = _extract_first(
            rf"{re.escape(ncc)}\s+(.+?)(?:ABIDJAN|LIBREVILLE|DOUALA|YAOUNDE|\d{{2}}/\d{{2}}/\d{{4}})",
            compact,
            flags=re.IGNORECASE,
        )
    if not activite:
        activite = _extract_first(r"Objet ou activite\s*:\s*(.+?)STATUT DES ETATS FINANCIERS", compact, flags=re.IGNORECASE)

    boite_postale = _extract_first(r"(\d{2}\s*BP\s*\d+\s*[A-Z]{2,6}\s*\d*)", compact, flags=re.IGNORECASE)
    code_postal = _extract_first(r"(\d{2}\s*BP\s*\d+)", compact, flags=re.IGNORECASE)
    client_nom = _extract_first(r"Oui\s+([A-Z][A-Z\s'\-]{6,})\s+GERANT", compact, flags=re.IGNORECASE)

    adresse_additional = ""
    if activite:
        adresse_additional = _extract_first(
            rf"{re.escape(activite)}\s+([A-Z0-9\-\s']+?)\s+\d{{2}}\s*BP",
            compact,
            flags=re.IGNORECASE,
        )

    ville = _extract_first(r"\b([A-Z][A-Z'\-\s]+)\s*\(VILLE\)\b", compact)
    if not ville:
        for city_hint in ["ABIDJAN", "LIBREVILLE", "DOUALA", "YAOUNDE", "POINTE-NOIRE", "BRAZZAVILLE"]:
            if re.search(rf"\b{re.escape(city_hint)}\b", compact, flags=re.IGNORECASE):
                ville = city_hint
                break

    date_reception = _parse_date_from_text(compact)

    country_hint = ""
    if re.search(r"\bABIDJAN\b|\+\(?225\)?", compact, flags=re.IGNORECASE):
        country_hint = "CI"
    elif re.search(r"\bLIBREVILLE\b|\+\(?241\)?", compact, flags=re.IGNORECASE):
        country_hint = "GA"
    elif re.search(r"\bDOUALA\b|\bYAOUNDE\b|\+\(?237\)?", compact, flags=re.IGNORECASE):
        country_hint = "CM"

    return {
        "raison_sociale": raison_sociale or "SOCIETE SANS NOM",
        "year": year,
        "liasse_ref": liasse_ref,
        "ncc": ncc,
        "rccm": rccm,
        "phone": phone,
        "email": email,
        "provider": provider,
        "activite": activite,
        "boite_postale": boite_postale,
        "code_postal": code_postal,
        "client_nom": client_nom,
        "adresse_additional": adresse_additional,
        "ville": ville.title() if ville else "",
        "date_reception": date_reception,
        "country_hint": country_hint,
    }


def _find_country(code):
    if not code:
        return None
    return (
        Pays.objects.filter(code__iexact=code).first()
        or Pays.objects.filter(nom__icontains=code).first()
    )


def _resolve_country(default_country_code, extracted_country_hint):
    pays = _find_country(extracted_country_hint)
    if pays:
        return pays

    pays = _find_country(default_country_code)
    if pays:
        return pays

    if (default_country_code or "").upper() == "CI":
        return (
            Pays.objects.filter(nom__icontains="ivoire").first()
            or Pays.objects.filter(nom__icontains="cote d'ivoire").first()
            or Pays.objects.filter(nom__icontains="cote ivoire").first()
        )
    return None


def _resolve_city(pays, city_name):
    if not pays:
        return None
    if city_name:
        ville = Ville.objects.filter(pays=pays, nom__iexact=city_name).first()
        if ville:
            return ville
        ville = Ville.objects.filter(pays=pays, nom__icontains=city_name).first()
        if ville:
            return ville

    return Ville.objects.filter(pays=pays).order_by("id").first()


class Command(BaseCommand):
    help = "Importe un ou plusieurs PDF fiscaux SYSCOHADA et genere acheteur + commande."

    def add_arguments(self, parser):
        parser.add_argument("--pdf", type=str, default="", help="Chemin du PDF a analyser.")
        parser.add_argument("--pdf-dir", type=str, default="", help="Dossier contenant des PDFs a importer.")
        parser.add_argument("--pattern", type=str, default="*.pdf", help="Pattern de fichiers pour --pdf-dir.")
        parser.add_argument("--dry-run", action="store_true", help="Analyse sans ecrire en base.")
        parser.add_argument(
            "--client-username",
            type=str,
            default="",
            help="Username client a forcer pour la commande (is_client=True).",
        )
        parser.add_argument(
            "--status",
            type=str,
            default="nouvelle",
            help="Statut initial de la commande (defaut: nouvelle).",
        )
        parser.add_argument(
            "--default-country-code",
            type=str,
            default="CI",
            help="Code pays par defaut si non detecte dans le PDF.",
        )

    def _collect_files(self, options):
        files = []

        one_file = (options.get("pdf") or "").strip()
        folder = (options.get("pdf_dir") or "").strip()
        pattern = (options.get("pattern") or "*.pdf").strip()

        if one_file:
            path = Path(one_file)
            if not path.exists() or not path.is_file():
                raise CommandError(f"PDF introuvable: {one_file}")
            files.append(path)

        if folder:
            folder_path = Path(folder)
            if not folder_path.exists() or not folder_path.is_dir():
                raise CommandError(f"Dossier introuvable: {folder}")
            files.extend(sorted(folder_path.glob(pattern)))

        dedup = []
        seen = set()
        for p in files:
            key = str(p.resolve())
            if key not in seen:
                seen.add(key)
                dedup.append(p)

        if not dedup:
            raise CommandError("Aucun fichier a traiter. Fournir --pdf ou --pdf-dir.")

        return dedup

    def _extract_text(self, pdf_path):
        try:
            import pypdf
        except Exception as exc:
            raise CommandError(f"Le package pypdf est requis: {exc}")

        reader = pypdf.PdfReader(str(pdf_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages[:20])

    def _resolve_client(self, pays, forced_username):
        if forced_username:
            user = User.objects.filter(username=forced_username, is_client=True).first()
            if not user:
                raise CommandError(f"client_username introuvable ou non client: {forced_username}")
            return user

        return (
            User.objects.filter(is_client=True, is_active=True, pays=pays).order_by("id").first()
            or User.objects.filter(is_client=True, is_active=True).order_by("id").first()
        )

    def _import_one(self, pdf_path, options):
        text = self._extract_text(pdf_path)
        if not text.strip():
            raise CommandError(f"Aucun texte exploitable trouve dans le PDF: {pdf_path}")

        data = _extract_data_from_text(text)

        self.stdout.write(self.style.NOTICE(f"\n[{pdf_path.name}] Informations extraites:"))
        for key in [
            "raison_sociale",
            "liasse_ref",
            "ncc",
            "rccm",
            "email",
            "phone",
            "ville",
            "country_hint",
            "date_reception",
        ]:
            self.stdout.write(f"- {key}: {data.get(key)}")

        if options["dry_run"]:
            return {"created": False, "updated": False, "commande_id": None, "acheteur_id": None}

        with transaction.atomic():
            pays = _resolve_country(options["default_country_code"], data["country_hint"])
            if not pays:
                raise CommandError(
                    "Impossible de determiner le pays. Utilisez --default-country-code ou completez les referentiels Pays."
                )

            ville = _resolve_city(pays, data["ville"])
            if not ville:
                province = Province.objects.filter(pays=pays).order_by("id").first()
                city_name = data["ville"] or "Ville inconnue"
                city_code = re.sub(r"[^A-Z]", "", city_name.upper())[:6] or "CITY"
                base_code = f"{city_code}-{(pays.code or 'XX').upper()}"
                final_code = base_code
                index = 1
                while Ville.objects.filter(code=final_code).exists():
                    index += 1
                    final_code = f"{base_code}-{index}"
                ville = Ville.objects.create(nom=city_name, code=final_code, pays=pays, province=province)

            categorie = CategorieEntreprise.objects.filter(active=True).order_by("id").first()
            forme = FormeJuridique.objects.order_by("id").first()
            statut = StatutEntreprise.objects.filter(active=True).order_by("id").first()

            acheteur_defaults = {
                "sigle": _clamp((data["raison_sociale"][:12] or "ACH"), 255).upper(),
                "email": _clamp(data["email"], 254),
                "activite_principale": _clamp(data["activite"], 255),
                "description": "Import automatique depuis PDF fiscal SYSCOHADA.",
                "numero_adresse": _clamp("12", 200),
                "rue_adresse": _clamp("Adresse extraite PDF", 200),
                "code_postal": _clamp(data["code_postal"], 200),
                "boite_postale": _clamp(data["boite_postale"], 200),
                "pays": pays,
                "ville": ville,
                "categorie_entreprise": categorie,
                "forme_juridique": forme,
                "statut_entreprise": statut,
                "commentaire": _clamp(
                    f"PDF import: NCC={data['ncc']}; RCCM={data['rccm']}; Ref={data['liasse_ref']}",
                    1000,
                ),
            }

            acheteur, _ = Acheteur.objects.update_or_create(
                nom=data["raison_sociale"],
                defaults=acheteur_defaults,
            )

            client = self._resolve_client(pays, (options.get("client_username") or "").strip())
            reference_client = data["liasse_ref"] or f"PDF-{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
            comments = _clamp(
                f"Import PDF fiscal {data['year']} NCC={data['ncc']} RCCM={data['rccm']}",
                100,
            )

            commande_defaults = {
                "notre_ref": _clamp(f"PDF-{timezone.now().strftime('%Y%m%d%H%M%S')}", 100),
                "raison_sociale": _clamp(data["raison_sociale"], 100),
                "type_rapport": "--------",
                "date_recept_commande": data["date_reception"] or timezone.localdate(),
                "date_rapport": timezone.localdate(),
                "delais": "10 jours",
                "priorite": "Normale",
                "numero_adresse": "12",
                "rue_adresse": _clamp("Adresse extraite PDF", 200),
                "code_postale_adresse": _clamp(data["code_postal"], 200),
                "telephone": _clamp(data["phone"], 100),
                "email": _clamp(data["email"], 100),
                "type_commande": "NORMALE",
                "type_traitement": "MANUEL",
                "client_nom": _clamp(data["client_nom"] or (client.get_full_name() if client else ""), 255),
                "company_identification_number": _clamp(data["rccm"], 100),
                "address_additional": _clamp(data["adresse_additional"], 100),
                "state": _clamp(ville.nom if ville else "", 100),
                "postcode": _clamp(data["code_postal"], 100),
                "post_office": _clamp(data["boite_postale"], 100),
                "provider": _clamp(data["provider"], 100),
                "comments": comments,
                "pays": pays,
                "ville": ville,
                "acheteur": acheteur,
                "client": client,
                "status": options["status"],
                "email_envoye": False,
            }

            commande, commande_created = Commande.objects.update_or_create(
                reference_client=reference_client,
                defaults=commande_defaults,
            )

            return {
                "created": commande_created,
                "updated": not commande_created,
                "commande_id": commande.id,
                "acheteur_id": acheteur.id,
                "reference_client": reference_client,
            }

    def handle(self, *args, **options):
        status_allowed = {choice[0] for choice in Commande.STATUS_CHOICES}
        if options["status"] not in status_allowed:
            raise CommandError(
                f"Status invalide '{options['status']}'. Valeurs autorisees: {', '.join(sorted(status_allowed))}"
            )

        files = self._collect_files(options)
        self.stdout.write(self.style.NOTICE(f"{len(files)} PDF(s) detecte(s)."))

        created_count = 0
        updated_count = 0
        errors = []

        for pdf_path in files:
            try:
                result = self._import_one(pdf_path, options)
                if options["dry_run"]:
                    self.stdout.write(self.style.WARNING(f"[DRY-RUN] {pdf_path.name} analyse avec succes."))
                else:
                    if result["created"]:
                        created_count += 1
                    else:
                        updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{pdf_path.name}: commande_id={result['commande_id']} acheteur_id={result['acheteur_id']} ref={result['reference_client']}"
                        )
                    )
            except Exception as exc:
                errors.append((pdf_path.name, str(exc)))
                self.stdout.write(self.style.ERROR(f"{pdf_path.name}: erreur -> {exc}"))

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry-run termine. Aucune ecriture effectuee."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Import termine: {created_count} creee(s), {updated_count} mise(s) a jour."))

        if errors:
            self.stdout.write(self.style.ERROR(f"{len(errors)} fichier(s) en erreur:"))
            for name, err in errors:
                self.stdout.write(self.style.ERROR(f"- {name}: {err}"))
            raise CommandError("Import partiellement termine avec erreurs.")
