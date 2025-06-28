from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.core'

    # def ready(self):
    #     import jet.utils
    #     from .patch_jet_menu import patched_get_menu_items
    #     jet.utils.get_menu_items = patched_get_menu_items
