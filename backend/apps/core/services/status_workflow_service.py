from backend.apps.core.utils.status_workflow.status_workflow_label_util import get_workflow_for_tenant, generate_labels_for_workflow
from backend.apps.core.utils.status_workflow.status_workflow_control_util import can_access_state, validate_transition
from core.models.tenant import CompanyTenant
from core.models.technician import Technician
from core.models.log import AuditLog
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from backend.apps.core.services.audition_log_service import log_service_order_status_transition
def create_status_workflow(tenant_id):
    tenant = CompanyTenant.objects.get(id=tenant_id)
    workflow = get_workflow_for_tenant(tenant)
    try:
        labeled_workflow = generate_labels_for_workflow(workflow)
    except AttributeError as error:
        return error
    return labeled_workflow

def transition_service_order_status(service_order, new_status: str, technician: Technician):
    tenant = service_order.tenant 
    technician_permission = technician.technician_permission 
    current_status = service_order.status

    workflow = get_workflow_for_tenant(tenant)

    if not validate_transition(workflow, current_status, new_status):
        raise ValidationError(f"Transition from '{current_status}' to '{new_status}' not allowed.")

    if not can_access_state(workflow, technician_permission, new_status):
        raise PermissionDenied(f"Permission Level '{technician_permission}' cannot access the state '{new_status}'.")

    service_order.status_history.append({
        "from": current_status,
        "to": new_status,
        "changed_by": str(technician),
        "timestamp": timezone.now().isoformat()
    })

    log_service_order_status_transition(service_order,new_status)

    return service_order
