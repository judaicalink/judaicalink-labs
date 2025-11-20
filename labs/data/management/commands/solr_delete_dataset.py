# labs/data/management/commands/solr_delete_dataset.py
import pysolr
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.safestring import mark_safe
from data.models import Dataset


class Command(BaseCommand):
    help = "Löscht alle Dokumente eines Datasets (dataslug) aus dem SOLR-Index."

    def add_arguments(self, parser):
        parser.add_argument("slug", type=str)

    def handle(self, *args, **options):
        slug = options["slug"]

        # Dataset auflösen, damit wir den echten dataslug kennen
        ds = None
        try:
            ds = Dataset.objects.get(name=slug)
        except Dataset.DoesNotExist:
            try:
                ds = Dataset.objects.get(dataslug=slug)
            except Dataset.DoesNotExist:
                ds = None

        dataslug = ds.dataslug or ds.name if ds else slug

        core_url = f"{settings.SOLR_SERVER.rstrip('/')}/{settings.JUDAICALINK_INDEX.lstrip('/')}"
        self.stdout.write(f'Lösche SOLR-Dokumente mit dataslug:"{dataslug}" aus {core_url}')

        solr = pysolr.Solr(core_url, timeout=60)
        try:
            solr.delete(q=f'dataslug:"{dataslug}"')
            solr.commit()
        except Exception as e:
            raise CommandError(mark_safe(f"Solr-Delete für {dataslug} fehlgeschlagen: {e}"))