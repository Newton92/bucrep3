from django.core.management.base import BaseCommand, CommandError
from main.models import Pays, Region, Ville


class Command(BaseCommand):
    help = "Importe les régions et villes du Gabon (id=2), Ghana (id=1) et Mali (id=5)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pays",
            nargs="+",
            type=int,
            choices=[1, 2, 5],
            default=[1, 2, 5],
            help="IDs des pays à importer (1=Ghana, 2=Gabon, 5=Mali). Défaut : tous.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulation sans écriture en base.",
        )

    def handle(self, *args, **options):
        pays_ids = options["pays"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN — aucune donnée écrite."))

        for pays_id in pays_ids:
            if pays_id not in DATA:
                self.stderr.write(self.style.ERROR(f"Pas de données pour pays id={pays_id}"))
                continue

            try:
                pays = Pays.objects.get(id=pays_id)
            except Pays.DoesNotExist:
                raise CommandError(
                    f"Pays id={pays_id} introuvable en base. Vérifiez que le pays existe."
                )

            self.stdout.write(self.style.NOTICE(f"\n=== {pays.nom.upper()} (id={pays_id}) ==="))
            self._import_pays(pays, DATA[pays_id], dry_run)

        self.stdout.write(self.style.SUCCESS("\n✔ Import terminé."))

    def _import_pays(self, pays, data, dry_run):
        regions_crees = regions_existants = villes_crees = villes_existantes = 0

        for code_region, region_data in data.items():
            if dry_run:
                self.stdout.write(f"  [REGION] {region_data['nom']} ({code_region})")
                for ville_nom in region_data["villes"]:
                    self.stdout.write(f"     └─ [VILLE] {ville_nom}")
                continue

            region, created = Region.objects.get_or_create(
                nom=region_data["nom"],
                pays=pays,
                defaults={"code": code_region, "is_active": True},
            )

            if created:
                regions_crees += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  [REGION] {region.nom} — créée")
                )
            else:
                regions_existants += 1
                self.stdout.write(f"  [REGION] {region.nom} — existante")

            for ville_nom in region_data["villes"]:
                ville, v_created = Ville.objects.get_or_create(
                    nom=ville_nom,
                    pays=pays,
                    defaults={
                        "code": ville_nom[:5].upper().replace(" ", "").replace("-", ""),
                        "is_active": True,
                    },
                )
                if v_created:
                    villes_crees += 1
                    self.stdout.write(f"     └─ [VILLE] {ville.nom} — créée")
                else:
                    villes_existantes += 1
                    self.stdout.write(f"     └─ [VILLE] {ville.nom} — existante")

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  → {regions_crees} région(s) créée(s), {regions_existants} existante(s)"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  → {villes_crees} ville(s) créée(s), {villes_existantes} existante(s)"
                )
            )


# ---------------------------------------------------------------------------
# DONNÉES
# ---------------------------------------------------------------------------

DATA = {
    # -----------------------------------------------------------------------
    # GHANA  (pays id=1)
    # -----------------------------------------------------------------------
    1: {
        "GAR": {
            "nom": "Greater Accra",
            "villes": ["Accra", "Tema", "Kasoa", "Ashaiman", "Madina"],
        },
        "AR": {
            "nom": "Ashanti",
            "villes": ["Kumasi", "Obuasi", "Ejisu", "Konongo", "Mampong"],
        },
        "WR": {
            "nom": "Western",
            "villes": ["Sekondi-Takoradi", "Tarkwa", "Prestea", "Axim", "Shama"],
        },
        "CR": {
            "nom": "Central",
            "villes": ["Cape Coast", "Mankessim", "Agona Swedru", "Elmina", "Assin Fosu"],
        },
        "ER": {
            "nom": "Eastern",
            "villes": ["Koforidua", "Nkawkaw", "Suhum", "Akim Oda", "Nsawam"],
        },
        "VR": {
            "nom": "Volta",
            "villes": ["Ho", "Hohoe", "Keta", "Aflao", "Kpando"],
        },
        "BR": {
            "nom": "Bono",
            "villes": ["Sunyani", "Berekum", "Dormaa Ahenkro", "Techiman", "Nkoranza"],
        },
        "BER": {
            "nom": "Bono East",
            "villes": ["Techiman", "Nkoranza", "Kintampo", "Atebubu", "Yeji"],
        },
        "AHR": {
            "nom": "Ahafo",
            "villes": ["Goaso", "Kukuom", "Bechem", "Hwidiem", "Mim"],
        },
        "NR": {
            "nom": "Northern",
            "villes": ["Tamale", "Yendi", "Savelugu", "Gushegu", "Kumbungu"],
        },
        "SVR": {
            "nom": "Savannah",
            "villes": ["Damongo", "Salaga", "Bole", "Buipe", "Sawla"],
        },
        "NER": {
            "nom": "North East",
            "villes": ["Nalerigu", "Walewale", "Gambaga", "Yunyo", "Bunkpurugu"],
        },
        "UER": {
            "nom": "Upper East",
            "villes": ["Bolgatanga", "Navrongo", "Bawku", "Zebilla", "Sandema"],
        },
        "UWR": {
            "nom": "Upper West",
            "villes": ["Wa", "Lawra", "Nandom", "Jirapa", "Tumu"],
        },
        "OTR": {
            "nom": "Oti",
            "villes": ["Dambai", "Jasikan", "Kadjebi", "Nkwanta", "Worawora"],
        },
        "WNR": {
            "nom": "Western North",
            "villes": ["Sefwi Wiawso", "Bibiani", "Enchi", "Juaboso", "Akontombra"],
        },
    },

    # -----------------------------------------------------------------------
    # GABON  (pays id=2)
    # -----------------------------------------------------------------------
    2: {
        "EST": {
            "nom": "Estuaire",
            "villes": ["Libreville", "Owendo", "Akanda", "Ntoum", "Cocobeach"],
        },
        "HO": {
            "nom": "Haut-Ogooué",
            "villes": ["Franceville", "Moanda", "Mounana", "Bakoumba", "Léconi"],
        },
        "MO": {
            "nom": "Moyen-Ogooué",
            "villes": ["Lambaréné", "Ndjolé", "Sindara"],
        },
        "NG": {
            "nom": "Ngounié",
            "villes": ["Mouila", "Fougamou", "Malinga", "Ndendé", "Mbigou"],
        },
        "NY": {
            "nom": "Nyanga",
            "villes": ["Tchibanga", "Mayumba", "Moabi", "Ndindi"],
        },
        "OI": {
            "nom": "Ogooué-Ivindo",
            "villes": ["Makokou", "Booué", "Mékambo", "Ovan"],
        },
        "OL": {
            "nom": "Ogooué-Lolo",
            "villes": ["Koulamoutou", "Lastoursville", "Pana", "Iboundji"],
        },
        "OM": {
            "nom": "Ogooué-Maritime",
            "villes": ["Port-Gentil", "Omboué", "Gamba", "Mandji"],
        },
        "WN": {
            "nom": "Woleu-Ntem",
            "villes": ["Oyem", "Bitam", "Minvoul", "Mitzic", "Eboro"],
        },
    },

    # -----------------------------------------------------------------------
    # MALI  (pays id=5)
    # -----------------------------------------------------------------------
    5: {
        "KY": {
            "nom": "Kayes",
            "villes": ["Kayes", "Kita", "Bafoulabé", "Kéniéba", "Diéma", "Yélimané"],
        },
        "KK": {
            "nom": "Koulikoro",
            "villes": ["Koulikoro", "Kati", "Kolokani", "Nara", "Dioïla", "Banamba"],
        },
        "SK": {
            "nom": "Sikasso",
            "villes": ["Sikasso", "Bougouni", "Koutiala", "Yanfolila", "Kadiolo", "Kolondiéba"],
        },
        "SG": {
            "nom": "Ségou",
            "villes": ["Ségou", "San", "Bla", "Niono", "Barouéli", "Tominian"],
        },
        "MP": {
            "nom": "Mopti",
            "villes": ["Mopti", "Bandiagara", "Djenné", "Douentza", "Koro", "Tenenkou"],
        },
        "TB": {
            "nom": "Tombouctou",
            "villes": ["Tombouctou", "Goundam", "Diré", "Niafunké", "Gourma-Rharous"],
        },
        "GA": {
            "nom": "Gao",
            "villes": ["Gao", "Ansongo", "Bourem", "Ménaka"],
        },
        "KD": {
            "nom": "Kidal",
            "villes": ["Kidal", "Abeïbara", "Tessalit", "Tin-Essako"],
        },
        "TD": {
            "nom": "Taoudénit",
            "villes": ["Taoudénit", "Araouan", "Boudjbeha"],
        },
        "MK": {
            "nom": "Ménaka",
            "villes": ["Ménaka", "Andéramboukane", "Alata", "Inékar"],
        },
        "BAM": {
            "nom": "District de Bamako",
            "villes": ["Bamako", "Kalaban-Coro", "Mountougoula"],
        },
    },
}
