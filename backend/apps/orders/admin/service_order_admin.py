import nested_admin
from django.contrib import admin
from backend.apps.checklist.admin import ChecklistInline
from backend.apps.orders.models import ServiceOrder
from backend.apps.filehub.admin import ServiceOrderPhotoInline, ServiceOrderSignatureInline


class ServiceOrderInline(nested_admin.NestedStackedInline):
    model = ServiceOrder
    inlines = [ChecklistInline, ServiceOrderPhotoInline, ServiceOrderSignatureInline]
