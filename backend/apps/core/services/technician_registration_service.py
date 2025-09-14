from backend.apps.core.validators.technician_validator import validate_is_active, validate_social_name, validate_technician_permission, validate_username
from backend.apps.core.models.technician import Technician
from backend.apps.core.services.technician_permission_service import has_permission

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
        username=username,
        social_name=social_name,
        technician_permission=technician_permission,
        is_active=True
    )

    return technician, errors
