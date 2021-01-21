from django.core.management.base import BaseCommand, CommandError
from data import models
from pathlib import Path
import requests
import json

class Command(BaseCommand):
    help = "Synchronise dataset metadata from GitHub"

    def handle(self, *args, **options):
        try:
            Path("data/gh_datasets").mkdir(parents=True, exist_ok=True)
            gh_res = requests.get('https://api.github.com/repos/wisslab/judaicalink-site/contents/content/datasets')
            gh_datasets = json.loads(gh_res.content.decode('utf-8'))
            for gh_dataset in gh_datasets:
                self.stdout.write('Importing {}'.format(gh_dataset['name']))
                gh_ds_md = requests.get(gh_dataset['download_url'])
                with open('data/gh_datasets/{}'.format(gh_dataset['name']), 'wb') as f:
                    f.write(gh_ds_md.content)
                models.update_from_markdown(gh_dataset['name'])
        except Exception as e:
            raise CommandError(e)
