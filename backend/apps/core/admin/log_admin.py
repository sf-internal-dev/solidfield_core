

import nested_admin
from django.contrib import admin
from backend.apps.core.models import (
    AuditLog,
)

class AuditLogInline(nested_admin.NestedTabularInline):
    model = AuditLog
    extra = 0
