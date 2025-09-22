
import nested_admin
from django.contrib import admin
from backend.apps.core.models import (
    CompanyTenant,
    TenantStatusWorkflow,
    
)
from backend.apps.clients.admin import ClientInline
from backend.apps.orders.admin import WorkOrderInline
from backend.apps.clients.admin import ClientAdressInline
from backend.apps.checklist.admin import ChecklistTemplateInline
from backend.apps.core.admin import TechnicianInline, TemporaryDelegationInline, AuditLogInline


class TenantWorkflowStatusInline(nested_admin.NestedStackedInline):
    model = TenantStatusWorkflow
    extra = 0

@admin.register(CompanyTenant)
class CompanyTenantAdmin(nested_admin.NestedModelAdmin):
    list_display = ("name", "slug", "tenant_code", "is_active", "created_at")
    inlines = [
        TechnicianInline,
        TenantWorkflowStatusInline,
        ClientInline,
        TemporaryDelegationInline,
        ChecklistTemplateInline,
        WorkOrderInline,
        AuditLogInline
    ]