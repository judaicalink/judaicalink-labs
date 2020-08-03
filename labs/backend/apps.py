from django.apps import AppConfig


class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):
        from .models import ThreadTask
        for task in ThreadTask.objects.filter(is_done=False):
            task.is_done = True
            task.status_ok = False
            task.save()
            task.log("Error: Task was found running after startup, marked as done.")

