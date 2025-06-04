from django.core.management.base import BaseCommand
import subprocess

class Command(BaseCommand):
    help = 'Wrapper around the judaicalink-loader script.'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['load', 'unload', 'delete'])
        parser.add_argument('dataset', nargs='?', default='all')

    def handle(self, *args, **options):
        cmd = ['judaicalink-loader', options['action']]
        if options['dataset']:
            cmd.append(options['dataset'])
        subprocess.run(cmd, check=False)

