import nested_admin
from django.contrib import admin

from backend.apps.filehub.models.os_signature import WorkOrderSignature

class WorkOrderSignatureInline(nested_admin.NestedStackedInline):
    model = WorkOrderSignature
    extra = 0