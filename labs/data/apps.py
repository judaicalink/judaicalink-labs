from django.apps import AppConfig


class DataConfig(AppConfig):
    name = 'data'
    default_auto_field = 'django.db.models.BigAutoField'


class JlDatasetsConfig(AppConfig):
    name = "datasets"
    verbose_name = "JudaicaLink Datasets"


class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):
        '''
        This is executed once the backend app is fully loaded.
        If the server was ended with running tasks, they are still
        marked as running in the database. Therefore, we have to
        clean them.
        '''
        from .models import ThreadTask
        for task in ThreadTask.objects.filter(is_done=False):
            task.is_done = True
            task.status_ok = False
            task.save()
            task.log("Error: Task was found running after startup, marked as done.")

    def ready(self):
        '''
        This is executed once the backend app is fully loaded.
        If the server was ended with running tasks, they are still
        marked as running in the database. Therefore, we have to
        clean them.
        '''
        try:
            from .models import ThreadTask
            for task in ThreadTask.objects.filter(is_done=False):
                task.is_done = True
                task.status_ok = False
                task.save()
                task.log("Error: Task was found running after startup, marked as done.")
        except:
            print("No cleanup, probably database not yet migrated.")
