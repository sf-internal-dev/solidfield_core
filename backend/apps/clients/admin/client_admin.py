import nested_admin
from django.contrib import admin
from backend.apps.clients.models.client import Client, ClientAddress

class ClientAdressInline(nested_admin.NestedStackedInline):
    model = ClientAddress
    extra = 0



# class ClientAddressAdmin(admin.ModelAdmin):
#     list_display = ("client", "label", "city", "state", "zip_code")
#     search_fields = ("client__name", "label", "city", "state")
#     list_filter = ("state",)
