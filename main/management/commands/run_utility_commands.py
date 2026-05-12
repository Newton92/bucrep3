from collections import OrderedDict

from django.core.management import call_command, get_commands
from django.core.management.base import BaseCommand, CommandError


# Command groups ordered by practical utility.
GROUPS = OrderedDict(
    [
        (
            "security",
            [
                "seed_groups",
            ],
        ),
        (
            "core_referentials",
            [
                "import_couleurs_commentaires",
                "import_devises",
                "import_annees_civiles",
                "import_type_rapport",
                "import_statut_entreprise",
                "import_categorie_entreprise",
                "import_forme_juridique_simple",
                "import_avis_commercial",
            ],
        ),
        (
            "nomenclatures",
            [
                "import_category_naf",
                "import_code_naf",
                "import_nace_codes",
            ],
        ),
        (
            "scoring_models",
            [
                "import_modele_alarme",
                "import_modele_age_societe",
                "import_modele_avis_commercial",
                "import_modele_bail",
                "import_modele_bilan",
                "import_modele_comportement_jugement",
                "import_modele_comportement_paiement",
                "import_modele_notation",
            ],
        ),
        (
            "conditions",
            [
                "import_conditions_base",
                "import_conditions_fixed",
                "fix_conditions_relations",
                "init_conditions",
            ],
        ),
        (
            "trade_terms",
            [
                "import_incoterms_final",
                "import_liste_importation",
                "fix_and_import_incoterms",
            ],
        ),
        (
            "geography",
            [
                "import_geo_data",
                "import_province_pays",
                "import_province_in_ville",
                "import_province_complet",
                "import_provinces_api",
                "import_gabon_localites",
                "clean_geo_data",
                "update_dashboard_pays",
            ],
        ),
        (
            "organization",
            [
                "import_domaines_poste_entreprise",
                "import_locaux",
            ],
        ),
        (
            "maintenance",
            [
                "fix_safedelete_tables",
                "fix_soft_deleted_scorings",
                "cleanup_scoring",
                "fix_unicode_commands",
            ],
        ),
        (
            "mailing",
            [
                "setup_mailing_test",
                "fetch_bucrep_mails",
                "credendo_simple_fetch_mails",
                "credendo_fetch_mails",
                "bucrepcontact_test_fetch_mails",
                "bucrepcontact_fetch_mails",
            ],
        ),
        (
            "legacy_or_alternatives",
            [
                "import_forme_juridique",
                "import_modele_notation_simple",
                "import_nace_simple",
            ],
        ),
        (
            "dangerous",
            [
                "reset_commandes",
            ],
        ),
        (
            "dev_tools",
            [
                "create_conditions_migration",
            ],
        ),
    ]
)


class Command(BaseCommand):
    help = (
        "Run management commands sequentially by utility group. "
        "Use --list to inspect groups and commands."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--list",
            action="store_true",
            help="List utility groups and their commands, then exit.",
        )
        parser.add_argument(
            "--group",
            action="append",
            choices=list(GROUPS.keys()),
            help="Utility group to run. Can be used multiple times.",
        )
        parser.add_argument(
            "--command",
            action="append",
            help="Run a specific command name. Can be used multiple times.",
        )
        parser.add_argument(
            "--all-safe",
            action="store_true",
            help="Run all groups except 'dangerous'.",
        )
        parser.add_argument(
            "--include-dangerous",
            action="store_true",
            help="Allow dangerous group when used with --all-safe.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show execution plan without running commands.",
        )
        parser.add_argument(
            "--continue-on-error",
            action="store_true",
            help="Continue even if one command fails.",
        )

    def handle(self, *args, **options):
        if options["list"]:
            self._print_catalog()
            return

        selected_groups = options.get("group") or []
        selected_commands = options.get("command") or []
        all_safe = options.get("all_safe", False)
        include_dangerous = options.get("include_dangerous", False)
        dry_run = options.get("dry_run", False)
        continue_on_error = options.get("continue_on_error", False)

        execution_plan = []

        if all_safe:
            for group_name, commands in GROUPS.items():
                if group_name == "dangerous" and not include_dangerous:
                    continue
                execution_plan.extend(commands)

        for group_name in selected_groups:
            execution_plan.extend(GROUPS[group_name])

        execution_plan.extend(selected_commands)
        execution_plan = self._unique_keep_order(execution_plan)

        if not execution_plan:
            raise CommandError(
                "No command selected. Use --list, --group, --command, or --all-safe."
            )

        registered = get_commands()
        missing = [cmd for cmd in execution_plan if cmd not in registered]
        if missing:
            raise CommandError(f"Unknown command(s): {', '.join(missing)}")

        self.stdout.write(self.style.SUCCESS("Execution plan:"))
        for idx, cmd_name in enumerate(execution_plan, start=1):
            self.stdout.write(f"{idx:02d}. {cmd_name}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run enabled. No command executed."))
            return

        for idx, cmd_name in enumerate(execution_plan, start=1):
            self.stdout.write(f"[{idx}/{len(execution_plan)}] Running: {cmd_name}")
            try:
                call_command(cmd_name)
            except Exception as exc:
                message = f"Command failed: {cmd_name} -> {exc}"
                if continue_on_error:
                    self.stderr.write(self.style.WARNING(message))
                    continue
                raise CommandError(message) from exc

        self.stdout.write(self.style.SUCCESS("All selected commands finished."))

    def _print_catalog(self):
        self.stdout.write(self.style.SUCCESS("Utility groups:"))
        for group_name, commands in GROUPS.items():
            self.stdout.write(f"\n- {group_name} ({len(commands)}):")
            for cmd_name in commands:
                self.stdout.write(f"  - {cmd_name}")

    @staticmethod
    def _unique_keep_order(items):
        seen = set()
        result = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result
