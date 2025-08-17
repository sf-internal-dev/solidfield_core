from backend.apps.orders.models.work_order import WorkOrder
from backend.apps.core.utils.status_workflow.status_workflow_control_util import validate_transition, get_single_terminal_state
from backend.apps.core.services.status_workflow_service import transition_service_order_status
from backend.apps.core.services.audition_log_service import log_service_order_validation
# ->  Validates status workflow terminal state
# and returns a finalized service order with
# transition_service_order_status service order
def validate_service_order(service_order: WorkOrder):
    workflow = service_order.tenant.status_workflow.workflow_json
    terminal_state = get_single_terminal_state(workflow)

    service_order_with_transition = transition_service_order_status(workflow,service_order.status,terminal_state)
    if service_order_with_transition:
        log_service_order_validation(service_order_with_transition)
    return service_order_with_transition