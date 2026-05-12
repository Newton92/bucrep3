"""Import NACE codes from 'CODE NACE AVEC CLASSEMENT SPECIFIQUE.xls'."""
import os
import xlrd
from django.core.management.base import BaseCommand
from main.models import NaceSpecifique


class Command(BaseCommand):
    help = "Import NaceSpecifique data from Excel file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default=os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "..",
                "Documents", "CODE NACE AVEC CLASSEMENT SPECIFIQUE.xls"
            ),
            help="Path to the Excel file",
        )
        parser.add_argument("--clear", action="store_true", help="Clear existing records first")

    def handle(self, *args, **options):
        filepath = options["file"]
        if not os.path.exists(filepath):
            self.stderr.write(f"File not found: {filepath}")
            return

        if options["clear"]:
            deleted, _ = NaceSpecifique.objects.all().delete()
            self.stdout.write(f"Cleared {deleted} existing records.")

        wb = xlrd.open_workbook(filepath)
        ws = wb.sheet_by_index(0)

        cur_activity = ""
        cur_type = ""
        created = 0
        updated = 0
        skipped = 0

        for row_idx in range(1, ws.nrows):
            row = [str(ws.cell_value(row_idx, c)).strip() for c in range(ws.ncols)]

            # Forward-fill activity and type (merged cells appear as empty)
            if row[0]:
                cur_activity = row[0]
            if row[1]:
                cur_type = row[1]

            code = row[2]
            denomination = row[3]

            if not code or not denomination:
                skipped += 1
                continue

            obj, was_created = NaceSpecifique.objects.update_or_create(
                code=code,
                defaults={
                    "activity": cur_activity,
                    "type": cur_type,
                    "denomination": denomination,
                    "active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — created: {created}, updated: {updated}, skipped: {skipped}"
            )
        )
