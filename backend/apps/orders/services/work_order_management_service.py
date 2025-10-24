from __future__ import annotations
from backend.apps.orders.models.work_order import WorkOrder, WorkOrderStatusHistory
from backend.apps.core.models.technician import Technician
from backend.apps.core.models.tenant import CompanyTenant
from backend.apps.core.services.technician_permission_service import has_permission
from backend.apps.core.services.audition_log_service import log_work_order_assignment, log_work_order_reassignment
from typing import Optional, List, Tuple, Dict, Any
from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils import timezone

# -> Lists work orders with optional filtering by technician, status, or tenant
# Supports pagination and ordering
# Returns a list of work orders with basic information
def list_work_orders(*, technician_operating: Technician, technician_id: Optional[int] = None, 
                    status: Optional[str] = None, tenant_id: Optional[int] = None,
                    limit: int = 50, offset: int = 0) -> Tuple[List[WorkOrder], List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "view_work_orders")
    if not ok:
        return [], perm_errors
    
    # Build query
    queryset = WorkOrder.objects.filter(tenant=technician_operating.tenant)
    
    # Apply filters
    if technician_id:
        queryset = queryset.filter(assigned_to_id=technician_id)
    if status:
        queryset = queryset.filter(status=status)
    if tenant_id:
        queryset = queryset.filter(tenant_id=tenant_id)
    
    # Apply pagination and ordering
    work_orders = list(queryset.select_related('tenant', 'assigned_to', 'created_by').order_by('-created_at')[offset:offset + limit])
    
    return work_orders, errors

# -> Retrieves a specific work order with all its details
# Returns detailed work order information including status history
def get_work_order(*, technician_operating: Technician, work_order_id: int) -> Tuple[Optional[WorkOrder], List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "view_work_orders")
    if not ok:
        return None, perm_errors
    
    try:
        work_order = WorkOrder.objects.select_related('tenant', 'assigned_to', 'created_by').prefetch_related(
            Prefetch('workorderstatushistory_set', queryset=WorkOrderStatusHistory.objects.order_by('-created_at'))
        ).get(
            id=work_order_id,
            tenant=technician_operating.tenant
        )
    except WorkOrder.DoesNotExist:
        return None, ["work_order_not_found"]
    
    return work_order, errors

# -> Updates an existing work order's information
# Validates all provided fields and updates only the ones that are valid
# Returns the updated work order or None with error messages
@transaction.atomic
def update_work_order(*, technician_operating: Technician, work_order_id: int, **update_data) -> Tuple[Optional[WorkOrder], List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "manage_work_orders")
    if not ok:
        return None, perm_errors
    
    try:
        work_order = WorkOrder.objects.get(
            id=work_order_id,
            tenant=technician_operating.tenant
        )
    except WorkOrder.DoesNotExist:
        return None, ["work_order_not_found"]
    
    # Validate and update fields
    if "title" in update_data:
        work_order.title = update_data["title"]
    
    if "description" in update_data:
        work_order.description = update_data["description"]
    
    if "priority" in update_data:
        if update_data["priority"] in ['low', 'medium', 'high', 'urgent']:
            work_order.priority = update_data["priority"]
        else:
            errors.append("invalid_priority")
    
    if "status" in update_data:
        # Validate status transition
        if update_data["status"] in ['pending', 'assigned', 'in_progress', 'completed', 'cancelled']:
            work_order.status = update_data["status"]
            # Log status change
            WorkOrderStatusHistory.objects.create(
                work_order=work_order,
                status=update_data["status"],
                changed_by=technician_operating,
                notes=f"Status changed to {update_data['status']}"
            )
        else:
            errors.append("invalid_status")
    
    if "assigned_to" in update_data:
        if update_data["assigned_to"]:
            try:
                assigned_technician = Technician.objects.get(
                    id=update_data["assigned_to"],
                    tenant=technician_operating.tenant
                )
                work_order.assigned_to = assigned_technician
            except Technician.DoesNotExist:
                errors.append("technician_not_found")
        else:
            work_order.assigned_to = None
    
    if "due_date" in update_data:
        work_order.due_date = update_data["due_date"]
    
    if "location" in update_data:
        work_order.location = update_data["location"]
    
    if "notes" in update_data:
        work_order.notes = update_data["notes"]
    
    if errors:
        return None, errors
    
    work_order.save()
    return work_order, errors

# -> Assigns a work order to a technician
# Logs the assignment action
# Returns success status and error messages
@transaction.atomic
def assign_work_order(*, technician_operating: Technician, work_order_id: int, technician_id: int) -> Tuple[bool, List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "assign_work_orders")
    if not ok:
        return False, perm_errors
    
    try:
        work_order = WorkOrder.objects.get(
            id=work_order_id,
            tenant=technician_operating.tenant
        )
    except WorkOrder.DoesNotExist:
        return False, ["work_order_not_found"]
    
    try:
        technician = Technician.objects.get(
            id=technician_id,
            tenant=technician_operating.tenant
        )
    except Technician.DoesNotExist:
        return False, ["technician_not_found"]
    
    # Check if already assigned to the same technician
    if work_order.assigned_to_id == technician_id:
        return True, []  # Already assigned, no error
    
    # Log assignment
    if work_order.assigned_to:
        log_work_order_reassignment(
            tenant=technician_operating.tenant,
            work_order=work_order,
            technician=technician
        )
    else:
        log_work_order_assignment(
            work_order=work_order,
            technician=technician,
            tenant=technician.tenant
        )
    
    # Update assignment
    work_order.assigned_to = technician
    work_order.status = 'assigned'
    work_order.save()
    
    # Log status change
    WorkOrderStatusHistory.objects.create(
        work_order=work_order,
        status='assigned',
        changed_by=technician_operating,
        notes=f"Work order assigned to {technician.social_name}"
    )
    
    return True, errors

# -> Gets the status history for a work order
# Returns chronological list of status changes
def get_work_order_status_history(*, technician_operating: Technician, work_order_id: int) -> Tuple[Optional[List[Dict]], List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "view_work_orders")
    if not ok:
        return None, perm_errors
    
    try:
        work_order = WorkOrder.objects.get(
            id=work_order_id,
            tenant=technician_operating.tenant
        )
    except WorkOrder.DoesNotExist:
        return None, ["work_order_not_found"]
    
    # Get status history
    status_history = WorkOrderStatusHistory.objects.filter(
        work_order=work_order
    ).select_related('changed_by').order_by('-created_at')
    
    history_data = []
    for entry in status_history:
        history_data.append({
            "id": entry.id,
            "status": entry.status,
            "changed_by": {
                "id": entry.changed_by.id,
                "username": entry.changed_by.username,
                "social_name": entry.changed_by.social_name
            },
            "notes": entry.notes,
            "created_at": entry.created_at.isoformat()
        })
    
    return history_data, errors
