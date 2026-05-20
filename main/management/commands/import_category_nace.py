"""
Peuple CategoryNaceCode et SubCategoryNaceCode depuis NaceSpecifique.

Structure :
  Étape 1 — Catégorie  : CategoryNaceCode  (unique par activity)
  Étape 2 — Groupe     : préfixe type extrait du code (code.split('.')[0])
  Étape 3 — Code NACE  : SubCategoryNaceCode  code="TYPE.ORIGINAL_CODE"

Exemple :
  NaceSpecifique(activity="01 - Agriculture...", type="A - Manufacturers", code="0100")
  →  CategoryNaceCode(code="01",  libelle="Agriculture and Fishing")
  →  SubCategoryNaceCode(code="A.0100",  libelle="Agriculture, hunting...",  category=cat)
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import CategoryNaceCode, NaceSpecifique, SubCategoryNaceCode


TYPE_PREFIX_MAP = {
    "A - Manufacturers":        "A",
    "B - Wholesalers & Agents": "B",
    "C - Retailers":            "C",
    "D - Services & other":     "D",
    "Other Public Services":    "OPS",
}


def _type_prefix(type_str: str) -> str:
    """Retourne le préfixe court pour un type NACE."""
    return TYPE_PREFIX_MAP.get(type_str.strip(), type_str.split(" - ")[0].strip() or "X")


def _activity_parts(activity: str):
    """Retourne (code_court, libelle) depuis une chaîne '01 - Agriculture...'."""
    parts = activity.split(" - ", 1)
    code = parts[0].strip()
    libelle = parts[1].strip() if len(parts) > 1 else activity.strip()
    return code, libelle


class Command(BaseCommand):
    help = "Importe CategoryNaceCode et SubCategoryNaceCode depuis NaceSpecifique"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait importé sans rien sauvegarder.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Vide CategoryNaceCode et SubCategoryNaceCode avant l'import.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        clear = options["clear"]

        nace_qs = NaceSpecifique.objects.filter(active=True).order_by(
            "activity", "type", "code"
        )
        total = nace_qs.count()
        self.stdout.write(f"NaceSpecifique actifs : {total}")

        if total == 0:
            self.stdout.write(self.style.WARNING("Aucun enregistrement à importer."))
            return

        if dry_run:
            self._preview(nace_qs)
            return

        with transaction.atomic():
            if clear:
                sub_count = SubCategoryNaceCode.all_objects.count()
                cat_count = CategoryNaceCode.all_objects.count()
                SubCategoryNaceCode.all_objects.all().delete()
                CategoryNaceCode.all_objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(
                        f"Tables vidées : {cat_count} catégorie(s), {sub_count} sous-catégorie(s)."
                    )
                )

            # ── Étape 1 : Catégories (unique par activity) ─────────────────
            cat_cache: dict[str, CategoryNaceCode] = {}
            activities = (
                nace_qs.values_list("activity", flat=True).distinct().order_by("activity")
            )
            cat_created = cat_skipped = 0
            for activity in activities:
                code, libelle = _activity_parts(activity)
                cat, created = CategoryNaceCode.objects.get_or_create(
                    code=code,
                    defaults={"libelle": libelle, "active": True, "poids": 0.0},
                )
                cat_cache[activity] = cat
                if created:
                    cat_created += 1
                else:
                    cat_skipped += 1

            self.stdout.write(
                f"Catégories : {cat_created} créée(s), {cat_skipped} existante(s)."
            )

            # ── Étape 2 : Sous-catégories ──────────────────────────────────
            sub_created = sub_skipped = sub_error = 0
            for nace in nace_qs:
                cat = cat_cache.get(nace.activity)
                if not cat:
                    sub_error += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Catégorie introuvable pour activity='{nace.activity}' (code={nace.code})"
                        )
                    )
                    continue

                prefix = _type_prefix(nace.type)
                sub_code = f"{prefix}.{nace.code}"

                sub, created = SubCategoryNaceCode.objects.get_or_create(
                    code=sub_code,
                    defaults={
                        "category": cat,
                        "libelle": nace.denomination,
                        "active": nace.active,
                        "poids": 0.0,
                    },
                )
                if not created and sub.category_id != cat.id:
                    sub.category = cat
                    sub.libelle = nace.denomination
                    sub.save(update_fields=["category", "libelle"])

                if created:
                    sub_created += 1
                else:
                    sub_skipped += 1

            self.stdout.write(
                f"Sous-catégories : {sub_created} créée(s), {sub_skipped} existante(s), "
                f"{sub_error} erreur(s)."
            )

        self.stdout.write(self.style.SUCCESS("Import terminé."))

    def _preview(self, nace_qs):
        seen_cats: set[str] = set()
        self.stdout.write("\n--- PREVIEW (dry-run) ---")
        for n in nace_qs[:20]:
            code, libelle = _activity_parts(n.activity)
            prefix = _type_prefix(n.type)
            sub_code = f"{prefix}.{n.code}"
            if code not in seen_cats:
                self.stdout.write(
                    f"[CAT]  code={code!r:6}  libelle={libelle!r}"
                )
                seen_cats.add(code)
            self.stdout.write(
                f"  [SUB]  code={sub_code!r:16}  libelle={n.denomination[:60]!r}"
            )
        self.stdout.write(f"\n... (affichage limité à 20 sur {nace_qs.count()})")
