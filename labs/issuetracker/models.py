import uuid as uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Issue(models.Model):
    #id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    description = models.TextField()
    triple = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=255)
    status = models.CharField(max_length=255, default='Open')
    priority = models.CharField(max_length=255, default='Low')
    github_issue_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.description
