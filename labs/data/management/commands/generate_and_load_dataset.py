import subprocess
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from data import models
from labs import settings


class Command(BaseCommand):
    help = "Generates a dataset (including metadata) and loads it into Fuseki."

    def add_arguments(self, parser):
        parser.add_argument(
            "dataslug",
            type=str,
            help="Slug of the dataset(slug oder name, without .md)",
        )

    def handle(self, *args, **options):
        slug = options["dataslug"]
        filename = f"{slug}.md"

        # 1. Read the metadata from the markdown file
        try:
            self.stdout.write(f"update_from_markdown({filename}) …")
            models.update_from_markdown(filename)
        except Exception as e:
            raise CommandError(f"update_from_markdown({filename}) failed: {e}")

        # Here we call the external build script
        self.stdout.write(f"Generating dataset {slug} …")

        try:
            subprocess.run(
                ["python", f"{slug}/scripts/build.py"],
                cwd=settings.GENERATORS_BASE_DIR,
                check=True,
            )

        except Exception as e:
            raise CommandError(f"Generating dataset {slug} failed: {e}")

        # 2. Load dataset into Fuseki
        try:
            self.stdout.write(f"fuseki_loader load {slug} …")
            call_command("fuseki_loader", "load", slug)
        except Exception as e:
            raise CommandError(f"Fuseki load of {slug} failed: {e}")
