from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from data import models
from pathlib import Path
import requests
import json
from django.conf import settings


class Command(BaseCommand):
    help = "Synchronise dataset metadata from GitHub"

    def handle(self, *args, **options):
        api_url = getattr(
            settings,
            "DATASETS_GITHUB_API_URL",
            "https://api.github.com/repos/judaicalink/judaicalink-site/contents/content/datasets",
        )

        gh_res = requests.get(api_url)
        gh_res.raise_for_status()
        gh_datasets = json.loads(gh_res.content.decode("utf-8"))

        Path(settings.HUGO_DIR).mkdir(parents=True, exist_ok=True)

        for gh_dataset in gh_datasets:
            self.stdout.write(f"Importing {gh_dataset['name']}")
            gh_ds_md = requests.get(gh_dataset["download_url"])
            gh_ds_md.raise_for_status()

            target = Path(settings.HUGO_DIR) / gh_dataset["name"]
            with open(target, "wb") as f:
                f.write(gh_ds_md.content)

            dataset = models.update_from_markdown(gh_dataset["name"])

            #  AUTOLOAD
            # If the dataset is marked as autoload, load it into Fuseki & SOLR

            autoload = getattr(dataset, "autoload", False)

            if autoload:
                slug = dataset.dataslug or dataset.name
                self.stdout.write(self.style.NOTICE(
                    f"Autoload enabled for dataset '{slug}' – loading into Fuseki & SOLR..."
                ))

                # 1. Fuseki
                self.stdout.write(f"  -> Fuseki: fuseki_loader load {slug}")
                call_command("fuseki_loader", "load", slug)

                # 2. SOLR
                self.stdout.write(f"  -> SOLR: solr_load_dataset {slug}")
                call_command("solr_load_dataset", slug)

        self.stdout.write(self.style.SUCCESS("sync_datasets finished."))