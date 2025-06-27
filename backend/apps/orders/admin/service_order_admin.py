import nested_admin
from django.contrib import admin
from backend.apps.checklist.admin import ChecklistInline
from backend.apps.orders.models import ServiceOrder


class ServiceOrderInline(nested_admin.NestedTabularInline):
    model = ServiceOrder
    inlines = [ChecklistInline]
