# import nested_admin
# from django.contrib import admin

import nested_admin
from django.contrib import admin
from backend.apps.core.models import (
    OfflineSyncQueue,
    
)

# class OfflineSyncQueueInline(nested_admin.)
class OfflineSyncQueueInline(nested_admin.NestedTabularInline):
    model = OfflineSyncQueue
    extra = 0
