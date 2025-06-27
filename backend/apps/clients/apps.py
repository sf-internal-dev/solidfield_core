from django.apps import AppConfig


class ClientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.clients'

    def ready(self):
        from .models import client, feedback


