from django.db import models
from datetime import datetime
# Create your models here.

class Dataset(models.Model):
    name = models.TextField()


class ThreadTask(models.Model):
    task = models.CharField(max_length=30, blank=True, null=True)
    is_done = models.BooleanField(blank=False, default=False)
    log_text = models.TextField()

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.log_text += timestamp + ": " + message + '\n'