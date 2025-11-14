from django.apps import AppConfig


class DataConfig(AppConfig):
    name = 'data'
    default_auto_field = 'django.db.models.BigAutoField'

class JlDatasetsConfig(AppConfig):
    name = "datasets"
    verbose_name = "JudaicaLink Datasets"
