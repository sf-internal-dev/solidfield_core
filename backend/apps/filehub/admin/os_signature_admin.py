import nested_admin
from django.contrib import admin

from backend.apps.filehub.models.os_signature import ServiceOrderSignature

class ServiceOrderSignatureInline(nested_admin.NestedStackedInline):
    model = ServiceOrderSignature
    extra = 0