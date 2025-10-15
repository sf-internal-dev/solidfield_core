from backend.apps.orders.models.work_order import WorkOrder
from backend.apps.core.models.technician import Technician
from backend.apps.core.services.audition_log_service import log_work_order_assignment,log_work_order_reassignment

def assign_work_order_to_technician(technician_operating: Technician, work_order: WorkOrder, technician: Technician):
    if work_order.assigned_to:
        log_work_order_assignment(work_order=work_order,technician=technician, tenant=technician.tenant)
        return work_order.assigned_to == technician
    
    log_work_order_reassignment(work_order=work_order,technician=technician)
    return work_order.assigned_to == technician