from backend.apps.core.models import AuditLog
from backend.apps.core.schemas import AUDIT_LOG_ACTION_SCHEMA
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now


def log_audit_action(technician, action_code: str, object_instance, context_data: dict = None):
    schema = AUDIT_LOG_ACTION_SCHEMA.get(action_code)
    if not schema:
        raise ValueError(f"Audition Log action '{action_code}' is not registered in the schema.")

    template = schema.get("template", "")
    description = schema.get("description", "")
    message = template.format(**context_data) if context_data else description
    
    AuditLog.objects.create(
        technician=technician,
        action=action_code,
        content_type=ContentType.objects.get_for_model(object_instance.__class__),
        object_id=str(object_instance.id),
        data=context_data,
        created_at=now()
    )

    return message  
