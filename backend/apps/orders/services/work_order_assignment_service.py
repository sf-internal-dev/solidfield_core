from backend.apps.orders.models.work_order import WorkOrder
from backend.apps.core.models.technician import Technician
from backend.apps.core.services.audition_log_service import log_service_order_assignment,log_service_order_reassignment

def assign_service_order_to_technician(service_order: WorkOrder, technician: Technician):
    if service_order.assigned_to:
        log_service_order_assignment(service_order=service_order,technician=technician)
        return service_order.assigned_to == technician
    
    log_service_order_reassignment(service_order=service_order,technician=technician)
    return service_order.assigned_to == technician