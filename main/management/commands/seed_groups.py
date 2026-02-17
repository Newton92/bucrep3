from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


GROUP_NAMES = [
    "Administrateur",
    "Analyste-Validateur",
    "Analyste-Validateur-Plus-Option-Envoyer-Mail",
    "Analyste-Simple",
    "Client",
]


class Command(BaseCommand):
    help = "Create or refresh default user groups."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete target groups before recreating them.",
        )

    def handle(self, *args, **options):
        reset = options.get("reset", False)

        if reset:
            deleted_count, _ = Group.objects.filter(name__in=GROUP_NAMES).delete()
            self.stdout.write(f"Deleted entries: {deleted_count}")

        created = []
        existing = []

        for name in GROUP_NAMES:
            _, was_created = Group.objects.get_or_create(name=name)
            if was_created:
                created.append(name)
            else:
                existing.append(name)

        if created:
            self.stdout.write(self.style.SUCCESS("Created groups:"))
            for name in created:
                self.stdout.write(f"- {name}")

        if existing:
            self.stdout.write(self.style.WARNING("Already existing groups:"))
            for name in existing:
                self.stdout.write(f"- {name}")

        self.stdout.write(self.style.SUCCESS("Done."))
