def is_assigned(service_order) -> bool:
    return True if service_order.technician else False

def reassign_service_order(service_order, new_technician):
    service_order.technician = new_technician
    return service_order

def assign_service_order(service_order, technician):
    if is_assigned(service_order):
        return reassign_service_order(service_order, technician)
    service_order.technician = technician
    return service_order
