

import nested_admin
from django.contrib import admin
from backend.apps.core.models import (
    Technician,
    DelegatedAction,
    TemporaryDelegation
)

from backend.apps.core.admin import OfflineSyncQueueInline

class TechnicianInline(nested_admin.NestedTabularInline):
    inlines = [OfflineSyncQueueInline]
    model = Technician
    extra = 0

class DelegatedActionInline(nested_admin.NestedTabularInline):
    model = DelegatedAction
    extra = 0
    
class TemporaryDelegationInline(nested_admin.NestedStackedInline):
    model = TemporaryDelegation
    inlines = [DelegatedActionInline]
    extra = 0


