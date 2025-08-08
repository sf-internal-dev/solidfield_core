from backend.apps.core.utils.status_workflow.status_workflow_label_util import get_workflow_for_tenant, generate_labels_for_workflow
from backend.apps.core.utils.status_workflow.status_workflow_control_util import (can_access_state, validate_transition,has_required_keys, validate_states, 
                                                                                  validate_permissions, validate_transitions, validate_single_terminal)
from core.models.tenant import CompanyTenant
from core.models.technician import Technician
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from backend.apps.core.services.audition_log_service import log_service_order_status_transition

# -> Receives custom workflow created by user and checks if it's valid
# If validation functions return False, then error logs are returned to a list
# If all validation functions return True, changes the tenant workflow for the custom workflow
def create_custom_status_workflow(tenant, custom_workflow: dict):
    errors = []
    is_valid, errs = has_required_keys(custom_workflow, {"states", "transitions", "permissions"})
    errors.extend(errs)
    if not is_valid:
        return False, errors

    # States
    states_ok, errs = validate_states(custom_workflow.get("states"))
    errors.extend(errs)
    declared_states = set(custom_workflow.get("states") or [])

    # Transitions
    transitions_ok, errs = validate_transitions(custom_workflow.get("transitions"), declared_states)
    errors.extend(errs)

    # Terminal
    terminal_ok, errs = validate_single_terminal(declared_states, custom_workflow.get("transitions", []))
    errors.extend(errs)

    # Permissions
    perms_ok, errs = validate_permissions(custom_workflow.get("permissions"), declared_states)
    errors.extend(errs)

    if states_ok and transitions_ok and terminal_ok and perms_ok:
        return tenant.status_workflow.workflow_json == custom_workflow

# -> Returns the status workflow for a given tenant (as labeled structure)
# Retrieves the tenant by ID and builds its custom workflow labels
# Returns an AttributeError if the workflow is malformed
def check_if_custom_status_workflow(tenant_id):
    tenant = CompanyTenant.objects.get(id=tenant_id)
    workflow = get_workflow_for_tenant(tenant)
    try:
        labeled_workflow = generate_labels_for_workflow(workflow)
    except AttributeError as error:
        return error
    return labeled_workflow

# -> Attempts to transition a service order from one status to another
# Validates if the transition is allowed by the workflow definition
# Also verifies if the technician has permission to reach the target status
# Appends the change to status_history and logs the transition
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
    current_status = new_status
    return service_order
