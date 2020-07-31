from django.core.management.base import BaseCommand
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create parsed dates from birthDate and deathDate'

    def handle(self, *args, **kwargs):
        self.stdout.write("There be dates!")
