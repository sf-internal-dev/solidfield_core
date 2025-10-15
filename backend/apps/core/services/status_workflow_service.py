from backend.apps.core.utils.status_workflow.status_workflow_label_util import get_workflow_for_tenant, generate_labels_for_workflow
from backend.apps.core.utils.status_workflow.status_workflow_control_util import (can_access_state, validate_transition,has_required_keys, validate_states, 
                                                                                  validate_permissions, validate_transitions, validate_single_terminal)
from core.models.tenant import CompanyTenant
from core.models.technician import Technician
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from backend.apps.core.services.audition_log_service import log_work_order_status_transition
from typing import Tuple, List, Optional

# -> Receives a custom workflow definition and validates its structure
# Validates required keys, states, transitions, terminal states, and permissions
# Accumulates all validation errors instead of stopping at the first failure
# If all validations pass, updates the tenant's workflow with the new custom definition
# Returns a tuple (success: bool, errors: List[str])
def create_custom_status_workflow(tenant, custom_workflow: dict) -> Tuple[bool, List[str]]:
    errors = []

    # Validate required keys
    is_valid, errs = has_required_keys(custom_workflow, {"states", "transitions", "permissions"})
    errors.extend(errs)

    states = custom_workflow.get("states") or []
    transitions = custom_workflow.get("transitions") or []
    permissions = custom_workflow.get("permissions") or []
    declared_states = set(states)

    # Validate workflow parts
    states_ok, errs = validate_states(states)
    errors.extend(errs)

    transitions_ok, errs = validate_transitions(transitions, declared_states)
    errors.extend(errs)

    terminal_ok, errs = validate_single_terminal(declared_states, transitions)
    errors.extend(errs)

    perms_ok, errs = validate_permissions(permissions, declared_states)
    errors.extend(errs)

    # Update workflow if valid
    if is_valid and states_ok and transitions_ok and terminal_ok and perms_ok:
        tenant.status_workflow.workflow_json = custom_workflow
        tenant.status_workflow.save()
        return True, errors

    return False, errors

# -> Returns the status workflow for a given tenant (as labeled structure)
# Retrieves the tenant by ID and builds its custom workflow labels
# Returns an AttributeError if the workflow is malformed
def check_if_custom_status_workflow(tenant_id) -> tuple[dict | None, list[str]]:
    errors: list[str] = []

    try:
        tenant = CompanyTenant.objects.get(id=tenant_id)
    except CompanyTenant.DoesNotExist:
        return None, ["tenant_not_found"]

    workflow = get_workflow_for_tenant(tenant)
    try:
        labeled = generate_labels_for_workflow(workflow)
    except AttributeError:
        return None, ["malformed_workflow"]

    return labeled, errors

# -> Attempts to transition a work order from one status to another
# Validates if the transition is allowed by the workflow definition
# Also verifies if the technician has permission to reach the target status
# Appends the change to status_history and logs the transition
def transition_work_order_status(technician_operating: Technician, work_order, new_status: str, technician: Technician)-> Tuple[Optional[object], List[str]]:
    errors: List[str] = []
    
    tenant = work_order.tenant
    current_status = work_order.status
    technician_permission = technician.technician_permission

    workflow = get_workflow_for_tenant(tenant)

    if not validate_transition(workflow, current_status, new_status):
        return None, [f"transition_not_allowed:{current_status}->{new_status}"]

    if not can_access_state(workflow, technician_permission, new_status):
        return None, [f"permission_denied_for_state:{new_status}"]

    entry = {
        "from": current_status,
        "to": new_status,
        "changed_by": str(technician),
        "timestamp": timezone.now().isoformat(),
    }
    history = list(work_order.status_history or [])
    history.append(entry)

    work_order.status_history = history
    work_order.status = new_status
    work_order.save(update_fields=["status", "status_history"])

    log_work_order_status_transition(tenant=technician_operating.tenant, work_order=work_order, new_status=new_status)

    return work_order, errors

