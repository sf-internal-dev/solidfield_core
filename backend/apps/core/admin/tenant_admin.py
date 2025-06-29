
import nested_admin
from django.contrib import admin
from backend.apps.core.models import (
    CompanyTenant,
    TenantWorkflow,
    
)
from backend.apps.clients.admin import ClientInline
from backend.apps.orders.admin import ServiceOrderInline
from backend.apps.clients.admin import ClientAdressInline
from backend.apps.checklist.admin import ChecklistTemplateInline
from backend.apps.core.admin import TechnicianInline, TemporaryDelegationInline, AuditLogInline


class TenantWorkflowInline(nested_admin.NestedStackedInline):
    model = TenantWorkflow
    extra = 0

@admin.register(CompanyTenant)
class CompanyTenantAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    inlines = [
        TechnicianInline,
        TenantWorkflowInline,
        ClientInline,
        TemporaryDelegationInline,
        ChecklistTemplateInline,
        ServiceOrderInline,
        AuditLogInline
    ]