from backend.apps.core.utils.status_workflow.status_workflow_label_util import get_workflow_for_tenant, generate_labels_for_workflow
from backend.apps.core.utils.status_workflow.status_workflow_control_util import can_access_state, validate_transition
from core.models.tenant import CompanyTenant
from core.models.log import AuditLog
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

""" Eu vou ter que fazer um service pra fazer a mudança de status da ordem de serviço,
    Utilizando utils como validade transition e can access state
"""

def create_status_workflow(tenant_id):
    tenant = CompanyTenant.objects.get(id=tenant_id)
    workflow = get_workflow_for_tenant(tenant)
    try:
        labeled_workflow = generate_labels_for_workflow(workflow)
    except AttributeError as error:
        return error
    return labeled_workflow

def transition_service_order_status(service_order, new_status: str, technician):
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

    # create log here.
    # pensar nesse action porque ele é no estilo de um workflow json também ou uma tag
    # reference_id pensar também porque isso é uma referencia direta ao id de algum model.
    AuditLog.objects.create(
        technician=technician,
        action="status_transition",
        content_type=ContentType.objects.get_for_model(service_order),
        object_id=str(service_order.id),
        data={"from": current_status, "to": new_status}
    )

    return service_order
