from backend.apps.checklist.services.checklist_service import create_checklist, save_answer, bulk_save_answers, remove_answer, list_missing_required_answers
from backend.apps.checklist.services.checklist_template_service import (next_order_for_template, remove_aggroupment_from_template, create_checklist_template, 
add_item_to_checklist_template, delegate_checklist_template_to_aggroupment, update_checklist_template_version,)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from backend.publisher import publish_ui_messages, get_client_ip
from backend.common.schemas.error_messages_schema import get_error_payload
import hashlib
from backend.apps.checklist.models import ChecklistTemplate, Checklist, ChecklistItemAnswer, ChecklistItemTemplate
from backend.apps.core.models import Technician, TechniciansAggroupment
from typing import Tuple, List, Optional
from backend.apps.core.services.technician_permission_service import has_permission

"""
class ChecklistTemplate(TenantOwnedModel, SoftDeletableModel):
    name = models.CharField(max_length=150)  # Ex: "Installing Standard Camera"
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(Technician, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    service_type = models.CharField(max_length=100)  # Ex: "Installing", "Maintenance"
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(default=True)

    aggroupments = models.ManyToManyField(
        TechniciansAggroupment,
        related_name="checklist_templates",
        blank=True,
    )

    class Meta:
        unique_together = ("tenant", "name", "version")

    def __str__(self):
        return f"{self.name} v{self.version} ({self.service_type})"

"""
@api_view(["POST"])
def create_checklist_template(request):
    data = request.data or {}
    
    technician_operating = getattr(request, "technician_operating", None)
    manager_account_operating = getattr(request, "manager_account_operating", None)

    name = data.get("name")
    service_type = data.get("service_type")

    aggroupment = data.get("aggroupment")

    checklist_template, messages = create_checklist_template(
        name = name,
        service_type = service_type,
        aggroupment = aggroupment if aggroupment else None
    )

    if messages:
        payloads = [get_error_payload(c) for c in messages]

        session_id = request.session.session_key or request.COOKIES.get("sessionid")
        client_ip = get_client_ip(request)

        ua = request.META.get("HTTP_USER_AGENT", "")
        client_fingerprint = hashlib.sha1(ua.encode()).hexdigest()[:16] if ua else None

        tenant_id = None
        if technician_operating is not None and getattr(technician_operating, "tenant", None) is not None:
            tenant_id = getattr(technician_operating.tenant, "id", None)

            correlation = publish_ui_messages(
            manager_account_operating_id=manager_account_operating,
            technician_operating_id=technician_operating,
            client_ip=client_ip,
            client_fingerprint=client_fingerprint,
            session_id=session_id,
            tenant_id=tenant_id,
            payloads=payloads,
            source="django_api",
        )
        return Response({"codes": messages, "correlation_id": correlation}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return Response({
        "success": "Checklist Template registered",
        "checklist_template_id":  str(checklist_template.id),
        "messages": messages,
        # talvez eu faça as funções register retornar um payload dos dados
    }, status=status.HTTP_201_CREATED)

def create_checklist():
    pass

def create_checklist_item_template():
    pass

def create_checklist_item_answer():
    pass