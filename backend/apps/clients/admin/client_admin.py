from django.contrib import admin
from backend.apps.clients.models.client import Client, ClientAddress

class ChecklistItemAnswerInline(admin.TabularInline):
    model = ClientAddress
    extra = 0

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    inlines = [ChecklistItemAnswerInline]
    list_display = ("name", "person_type", "document_id", "phone", "email", "created_at")
    search_fields = ("name", "document_id", "email", "phone", "contact_name")
    list_filter = ("person_type", "created_at")
    ordering = ("name",)
    list_select_related = True


# class ClientAddressAdmin(admin.ModelAdmin):
#     list_display = ("client", "label", "city", "state", "zip_code")
#     search_fields = ("client__name", "label", "city", "state")
#     list_filter = ("state",)
