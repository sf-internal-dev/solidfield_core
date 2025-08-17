import nested_admin
from django.contrib import admin
from backend.apps.checklist.admin import ChecklistInline
from backend.apps.orders.models import WorkOrder
from backend.apps.filehub.admin import WorkOrderPhotoInline, WorkOrderSignatureInline


class WorkOrderInline(nested_admin.NestedStackedInline):
    model = WorkOrder
    inlines = [ChecklistInline, WorkOrderPhotoInline, WorkOrderSignatureInline]
