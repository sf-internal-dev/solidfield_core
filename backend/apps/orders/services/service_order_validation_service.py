from backend.apps.orders.models.service_order import ServiceOrder
from backend.apps.core.utils.status_workflow.status_workflow_control_util import validate_transition, get_single_terminal_state
from backend.apps.core.services.status_workflow_service import transition_service_order_status

# ->  Validates status workflow terminal state
# and returns a finalized service order with
# transition_service_order_status service order
def validate_service_order(service_order: ServiceOrder):
    workflow = service_order.tenant.status_workflow.workflow_json
    terminal_state = get_single_terminal_state(workflow)
    
    return transition_service_order_status(workflow,service_order.status,terminal_state)