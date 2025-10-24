from backend.apps.core.validators.technician_validator import validate_is_active, validate_social_name, validate_technician_permission, validate_username
from backend.apps.core.models.technician import Technician
from backend.apps.core.services.technician_permission_service import has_permission
from typing import Tuple, List, Optional

def register_technician(technician_operating: Technician, username: str, social_name: str, technician_permission: str):
    errors = []
    ok, perms_errors = has_permission(technician_operating, "register_technician")
    if not ok:
        return None, perms_errors
    
    if not validate_social_name(value=social_name):
        errors.append("invalid_social_name")
    if not validate_username(value=username):
        errors.append("invalid_usename")
    if not validate_technician_permission(value=technician_permission):
        errors.append("invalid_technician_permission")

    if errors:
        return None, errors
    
    technician = Technician.objects.create(
        tenant=technician_operating.tenant,
        username=username,
        social_name=social_name,
        technician_permission=technician_permission,
        is_active=True
    )

    return technician, errors

# -> Updates an existing technician's information
# Validates all provided fields and updates only the ones that are valid
# Returns the updated technician or None with error messages
def update_technician(technician_operating: Technician, technician_id: int, **update_data) -> Tuple[Optional[Technician], List[str]]:
    errors = []
    
    # Check permission
    ok, perms_errors = has_permission(technician_operating, "manage_technicians")
    if not ok:
        return None, perms_errors
    
    try:
        technician = Technician.objects.get(id=technician_id, tenant=technician_operating.tenant)
    except Technician.DoesNotExist:
        return None, ["technician_not_found"]
    
    # Validate and update fields
    if "social_name" in update_data:
        if validate_social_name(update_data["social_name"]):
            technician.social_name = update_data["social_name"]
        else:
            errors.append("invalid_social_name")
    
    if "username" in update_data:
        if validate_username(update_data["username"]):
            technician.username = update_data["username"]
        else:
            errors.append("invalid_username")
    
    if "technician_permission" in update_data:
        if validate_technician_permission(update_data["technician_permission"]):
            technician.technician_permission = update_data["technician_permission"]
        else:
            errors.append("invalid_technician_permission")
    
    if "is_active" in update_data:
        if validate_is_active(update_data["is_active"]):
            technician.is_active = update_data["is_active"]
        else:
            errors.append("invalid_is_active")
    
    if "aggroupment" in update_data:
        technician.aggroupment_id = update_data["aggroupment"]
    
    if errors:
        return None, errors
    
    technician.save()
    return technician, errors

# -> Soft deletes a technician by setting is_active to False
# Only L3 technicians can delete other technicians
# Returns success status and error messages
def delete_technician(technician_operating: Technician, technician_id: int) -> Tuple[bool, List[str]]:
    errors = []
    
    # Check permission
    ok, perms_errors = has_permission(technician_operating, "manage_technicians")
    if not ok:
        return False, perms_errors
    
    try:
        technician = Technician.objects.get(id=technician_id, tenant=technician_operating.tenant)
    except Technician.DoesNotExist:
        return False, ["technician_not_found"]
    
    # Prevent self-deletion
    if technician.id == technician_operating.id:
        return False, ["cannot_delete_self"]
    
    technician.is_active = False
    technician.save()
    
    return True, errors
