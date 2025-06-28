import nested_admin
from django.contrib import admin

from backend.apps.filehub.models.os_photo import ServiceOrderPhoto

class ServiceOrderPhotoInline(nested_admin.NestedStackedInline):
    model = ServiceOrderPhoto
    extra = 0