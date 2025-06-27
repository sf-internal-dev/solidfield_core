import nested_admin
from django.contrib import admin
from backend.apps.core.models import (
    CompanyTenant,
    Technician,
    TenantWorkflow,
    TemporaryDelegation,
    DelegatedAction,
)
from backend.apps.clients.models import Client
from backend.apps.orders.admin import ServiceOrderInline

class DelegatedActionInline(nested_admin.NestedTabularInline):
    model = DelegatedAction
    extra = 0

class TemporaryDelegationInline(nested_admin.NestedStackedInline):
    model = TemporaryDelegation
    inlines = [DelegatedActionInline]
    extra = 0
class TechnicianInline(nested_admin.NestedTabularInline):
    model = Technician
    extra = 0





class TenantWorkflowInline(nested_admin.NestedStackedInline):
    model = TenantWorkflow
    extra = 0

class ClientInline(nested_admin.NestedTabularInline):
    model = Client
    extra = 0

# class OfflineSyncQueueInline(nested_admin.NestedTabularInline):
#     model = OfflineSyncQueue
#     extra = 0

@admin.register(CompanyTenant)
class CompanyTenantAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    inlines = [
        TechnicianInline,
        TenantWorkflowInline,
        ClientInline,
        TemporaryDelegationInline,
        ServiceOrderInline,
    ]
