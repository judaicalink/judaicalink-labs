import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from data import models
from labs import settings


class Command(BaseCommand):
    help = "Erzeugt ein Dataset neu (inkl. Metadaten) und lädt es in Fuseki."

    def add_arguments(self, parser):
        parser.add_argument(
            "dataslug",
            type=str,
            help="Slug des Datasets (dataslug oder name, ohne .md)",
        )

    def handle(self, *args, **options):
        slug = options["dataslug"]
        filename = f"{slug}.md"

        # 1. Metadaten aus der Markdown-Datei neu einlesen
        try:
            self.stdout.write(f"update_from_markdown({filename}) …")
            models.update_from_markdown(filename)
        except Exception as e:
            raise CommandError(f"update_from_markdown({filename}) fehlgeschlagen: {e}")

        # HIER kannst du, falls nötig, deinen externen Generator aus
        # judaicalink-generators aufrufen (z.B. via subprocess). Beispiel:
        #
        try:
            subprocess.run(
                ["python", f"{slug}/scripts/build.py" ],
                cwd=settings.GENERATORS_BASE_DIR,
                   check=True,
               )

        except Exception as e:
            raise CommandError()

        # 2. Dataset in Fuseki laden
        try:
            self.stdout.write(f"fuseki_loader load {slug} …")
            call_command("fuseki_loader", "load", slug)
        except Exception as e:
            raise CommandError(f"fuseki_loader load {slug} fehlgeschlagen: {e}")
