from data.models import Dataset
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Delete dataset from Fuseki, Solr, and Django."

    def add_arguments(self, parser):
        parser.add_argument("slug", type=str)

    def handle(self, *args, **options):
        slug = options["slug"]
        self.stdout.write(f"Delete dataset '{slug}' ...")

        try:
            ds = Dataset.objects.get(name=slug)
        except Dataset.DoesNotExist:
            raise CommandError(f"Dataset '{slug}' not found.")

        # 1. Löschen aus Fuseki
        self.stdout.write(f"→ Fuseki delete {slug}")
        call_command("fuseki_loader", "delete", slug)

        # 2. Löschen aus Solr
        self.stdout.write(f"→ Solr delete {slug}")
        call_command("solr_delete_dataset", slug)

        # 3. Django löschen
        self.stdout.write(f"→ Remove dataset from database")
        ds.delete()

        self.stdout.write(self.style.SUCCESS(f"Dataset '{slug}' fully deleted."))
