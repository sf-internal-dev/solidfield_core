import nested_admin
from django.contrib import admin

from backend.apps.filehub.models.os_photo import WorkOrderPhoto

class WorkOrderPhotoInline(nested_admin.NestedStackedInline):
    model = WorkOrderPhoto
    extra = 0