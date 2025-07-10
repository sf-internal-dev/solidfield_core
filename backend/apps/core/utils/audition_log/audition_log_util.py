from backend.apps.core.models import AuditLog
from backend.apps.core.schemas import AUDIT_LOG_ACTION_SCHEMA
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from django.apps import apps

def get_model_from_schema_entry(schema_entry: dict):
    app_label, model_name = schema_entry["model"].split(".")
    return apps.get_model(app_label=app_label, model_name=model_name)

def log_audit_action(technician, action_code: str, object_instance, context_data: dict = None):
    schema_entry = AUDIT_LOG_ACTION_SCHEMA.get(action_code)
    if not schema_entry:
        raise ValueError(f"Audition Log action '{action_code}' is not registered in the schema.")
    
    model_class = get_model_from_schema_entry(schema_entry)

    if not isinstance(object_instance, model_class):
        raise ValueError("Invalid model passed for audit action")
    
    template = schema_entry.get("template", "")
    description = schema_entry.get("description", "")
    message = template.format(**context_data) if context_data else description

    AuditLog.objects.create(
        technician=technician,
        action=action_code,
        content_type=ContentType.objects.get_for_model(model_class),
        object_id=str(object_instance.id),
        data={**(context_data or {}), "rendered_message": message},
        created_at=now()
    )

    return message  
