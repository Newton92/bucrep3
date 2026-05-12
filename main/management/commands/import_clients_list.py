from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

from main.models import Client, Pays


@dataclass(frozen=True)
class ClientSeed:
    nom: str
    website: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    explicit_email: Optional[str] = None


CLIENTS_TO_IMPORT = [
    ClientSeed(
        "OC AFRICA",
        website="https://a-ocl.com",
        country="Cote d'Ivoire",
        city="Abidjan",
    ),
    ClientSeed("BPI FRANCE", website="https://www.bpifrance.fr", country="France", city="Maisons-Alfort", phone="+33141798000"),
    ClientSeed("TRADE INSUR", country="United Kingdom"),
    ClientSeed(
        "CAGEX",
        website="http://www.cagex.dz",
        country="Algeria",
        city="Alger",
        phone="+21323312100",
        explicit_email="dir_generale@cagex.dz",
    ),
    ClientSeed("SMAEX", country="Morocco", city="Casablanca", phone="+212522982000"),
    ClientSeed("AKTIENGESELLSCHAFT", country="Germany", city="Hamburg"),
    ClientSeed("GESTION 360 CA", website="https://gestion360.ca", country="Canada", city="Windsor QC", phone="+18195881830"),
    ClientSeed("COTUNACE", website="https://www.cotunace.com.tn", country="Tunisia", city="Tunis", phone="+21671908600"),
    ClientSeed("ERIE EUROPE", website="https://www.erieeurope.eu", country="France", city="Paris", phone="+33153201170"),
    ClientSeed("INFORMASTRE", country="France"),
    ClientSeed("URIOS", website="https://urios.com", country="France", city="Paris", phone="+33143112828"),
    ClientSeed("CREDENDO", website="https://credendo.com", country="Belgium", city="Brussels", phone="+3227888755"),
    ClientSeed("DADSON", website="https://dadsonlaundry.com", country="United States"),
    ClientSeed("UNDERWRITING AFRICA", website="https://underwritingafrica.com", country="Kenya", city="Nairobi", phone="+254782636709"),
    ClientSeed("STRATEGIE INSIGHT", country="Mauritius", city="Beau Bassin"),
    ClientSeed("CFAO", website="https://www.cfaogroup.com", country="France", city="Boulogne-Billancourt", phone="+33146235656"),
    ClientSeed("INFORISK", website="https://inforisk.ma", country="Morocco", city="Casablanca", phone="+212522640077"),
    ClientSeed("CREDIT GUARANTEE", website="https://www.creditguarantee.co.za", country="South Africa", city="Sandton", phone="+27118897000"),
    ClientSeed("SORENCO SA", website="http://www.sorenco.com.tn", country="Tunisia", city="Tunis"),
    ClientSeed(
        "CONFIDEXIA CORPORATION",
        website="https://www.confidexia.com",
        country="United States",
        city="Miami",
        phone="+13052515250",
        explicit_email="info@confidexia.com",
    ),
    ClientSeed("VA INTER TRADING", website="https://vait.com", country="Austria", city="Linz", phone="+4373278040"),
    ClientSeed("INOXICO", website="https://www.inoxico.com", country="South Africa", phone="+27100072600", explicit_email="support@inoxico.com"),
    ClientSeed("ATRADIUS V", website="https://group.atradius.com", country="Netherlands", city="Amsterdam"),
    ClientSeed("CCI CREDIT MANAGEMENT", website="https://www.ccicm.com", country="United Kingdom", phone="+441766772288"),
    ClientSeed("SCANIA", website="https://www.scania.com", country="Sweden", city="Sodertalje", phone="+46855381000"),
    ClientSeed("ALLIANZ TRADE", website="https://www.allianz-trade.com", country="France"),
]

UNRESOLVED_CLIENTS = set()

COUNTRY_ALIASES = {
    "algeria": ["algerie"],
    "austria": ["autriche"],
    "belgium": ["belgique"],
    "canada": [],
    "cote d'ivoire": ["cote d ivoire", "ivory coast"],
    "france": [],
    "germany": ["allemagne"],
    "kenya": [],
    "morocco": ["maroc"],
    "mauritius": ["maurice"],
    "netherlands": ["pays-bas", "netherland"],
    "south africa": ["afrique du sud"],
    "sweden": ["suede"],
    "tunisia": ["tunisie"],
    "united kingdom": ["uk", "royaume-uni", "great britain"],
    "united states": ["usa", "etats-unis", "united states of america"],
}

COUNTRY_CODES = {
    "algeria": "DZ",
    "austria": "AT",
    "belgium": "BE",
    "canada": "CA",
    "cote d'ivoire": "CI",
    "france": "FR",
    "germany": "DE",
    "kenya": "KE",
    "morocco": "MA",
    "mauritius": "MU",
    "netherlands": "NL",
    "south africa": "ZA",
    "sweden": "SE",
    "tunisia": "TN",
    "united kingdom": "GB",
    "united states": "US",
}


class Command(BaseCommand):
    help = (
        "Importe/actualise des entreprises clientes dans Client et User "
        "(avec is_client=True)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--default-password",
            type=str,
            default="ChangeMe@12345",
            help="Mot de passe applique aux comptes User clients.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule l'import sans ecriture en base.",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Met a jour les enregistrements existants (sinon, skip).",
        )

    def handle(self, *args, **options):
        password = options["default_password"]
        dry_run = options["dry_run"]
        update_existing = options["update_existing"]

        User = get_user_model()

        created_clients = 0
        updated_clients = 0
        skipped_clients = 0
        created_users = 0
        updated_users = 0
        skipped_users = 0
        users_with_country = 0
        users_in_group = 0
        group_client, _ = Group.objects.get_or_create(name="Client")

        self.stdout.write(f"Import de {len(CLIENTS_TO_IMPORT)} clients...")
        if UNRESOLVED_CLIENTS:
            self.stdout.write(
                self.style.WARNING(
                    "Entrees a verifier manuellement (source stricte non trouvee): "
                    + ", ".join(sorted(UNRESOLVED_CLIENTS))
                )
            )

        with transaction.atomic():
            for seed in CLIENTS_TO_IMPORT:
                email = self._build_email(seed)
                address = self._build_address(seed)
                username = self._build_username(seed.nom, User, email)

                client_defaults = {
                    "nom": seed.nom,
                    "telephone": seed.phone,
                    "adresse": address,
                    "actif": True,
                }

                existing_client = Client.objects.filter(email=email).first()
                if existing_client and not update_existing:
                    skipped_clients += 1
                    client_obj = existing_client
                else:
                    client_obj, client_created = Client.objects.update_or_create(
                        email=email,
                        defaults=client_defaults,
                    )
                    if client_created:
                        created_clients += 1
                    else:
                        updated_clients += 1

                user_defaults = {
                    "email": email,
                    "first_name": seed.nom[:150],
                    "last_name": "Client",
                    "address": address,
                    "telephone": seed.phone,
                    "profession": "Entreprise cliente",
                    "role": "Client",
                    "is_client": True,
                    "activation": True,
                    "is_active": True,
                }
                resolved_pays = self._resolve_pays(seed.country)
                if resolved_pays:
                    user_defaults["pays"] = resolved_pays

                existing_user = User.objects.filter(username=username).first()
                if existing_user and not update_existing:
                    skipped_users += 1
                    user_obj = existing_user
                else:
                    user_obj, user_created = User.objects.update_or_create(
                        username=username,
                        defaults=user_defaults,
                    )
                    user_obj.set_password(password)
                    user_obj.save()
                    if user_created:
                        created_users += 1
                    else:
                        updated_users += 1

                if resolved_pays and (update_existing or not user_obj.pays_id):
                    user_obj.pays = resolved_pays
                user_obj.role = "Client"
                user_obj.is_client = True
                user_obj.save(update_fields=["pays", "role", "is_client"])

                user_obj.groups.add(group_client)
                if user_obj.pays_id:
                    users_with_country += 1
                if user_obj.groups.filter(id=group_client.id).exists():
                    users_in_group += 1

                self.stdout.write(
                    f"[OK] {seed.nom} | client_id={getattr(client_obj, 'id', None)} | "
                    f"user={username} | pays={getattr(user_obj.pays, 'nom', '-')}"
                )

            if dry_run:
                self.stdout.write(self.style.WARNING("DRY RUN -> rollback en cours..."))
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                "Termine - "
                f"Clients: {created_clients} crees, {updated_clients} maj, {skipped_clients} skip | "
                f"Users: {created_users} crees, {updated_users} maj, {skipped_users} skip | "
                f"Pays assignes: {users_with_country} | Groupe Client: {users_in_group}"
            )
        )

    def _build_email(self, seed: ClientSeed) -> str:
        if seed.explicit_email:
            return seed.explicit_email.lower()

        domain = self._domain_from_website(seed.website)
        if domain:
            return f"contact@{domain}".lower()

        return f"contact.{slugify(seed.nom)}@client.local".lower()

    def _build_address(self, seed: ClientSeed) -> Optional[str]:
        chunks = []
        if seed.street:
            chunks.append(seed.street)
        if seed.city:
            chunks.append(seed.city)
        if seed.country:
            chunks.append(seed.country)
        if seed.website:
            chunks.append(f"Site: {seed.website}")
        return ", ".join(chunks) if chunks else None

    def _build_username(self, company_name: str, user_model, email: str) -> str:
        base = slugify(company_name).replace("-", "_")
        if not base:
            base = "client"
        candidate = f"{base[:120]}_client"

        existing = user_model.objects.filter(username=candidate).first()
        if not existing:
            return candidate
        if getattr(existing, "is_client", False) or (existing.email or "").lower() == email.lower():
            return candidate

        suffix = 2
        while True:
            max_base = 150 - len(f"_client_{suffix}")
            alt = f"{base[:max_base]}_client_{suffix}"
            existing_alt = user_model.objects.filter(username=alt).first()
            if not existing_alt:
                return alt
            if getattr(existing_alt, "is_client", False) or (existing_alt.email or "").lower() == email.lower():
                return alt
            suffix += 1

    def _domain_from_website(self, website: Optional[str]) -> Optional[str]:
        if not website:
            return None
        cleaned = website.strip().lower()
        for prefix in ("https://", "http://"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        cleaned = cleaned.split("/")[0]
        if cleaned.startswith("www."):
            cleaned = cleaned[4:]
        return cleaned or None

    def _resolve_pays(self, raw_country: Optional[str]) -> Optional[Pays]:
        if not raw_country:
            return None

        normalized = (raw_country or "").strip().lower()
        canonical = normalized
        for key, aliases in COUNTRY_ALIASES.items():
            if normalized == key or normalized in aliases:
                canonical = key
                break

        code = COUNTRY_CODES.get(canonical)
        terms = {raw_country.strip(), canonical}
        for alias in COUNTRY_ALIASES.get(canonical, []):
            terms.add(alias)
        terms = {t for t in terms if t}

        query = Q()
        if code:
            query |= Q(code__iexact=code)
        for term in terms:
            query |= Q(nom__iexact=term)

        if query:
            pays = Pays.objects.filter(query).first()
            if pays:
                return pays

        if code:
            return Pays.objects.create(nom=raw_country.strip()[:50], code=code, is_active=True)
        return None
