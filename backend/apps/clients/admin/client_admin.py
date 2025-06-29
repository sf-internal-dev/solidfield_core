import nested_admin
from django.contrib import admin
from backend.apps.clients.models.client import Client, ClientAddress

class ClientAdressInline(nested_admin.NestedStackedInline):
    model = ClientAddress
    extra = 0


class ClientInline(nested_admin.NestedTabularInline):
    inlines = [ClientAdressInline]
    model = Client
    extra = 0
