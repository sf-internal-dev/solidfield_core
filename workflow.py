DEFAULT_WORKFLOW = {
    "states": ["open", "in_progress", "finished", "awaiting_validation", "approved"],
    "transitions": [
        {"from": "open", "to": "in_progress"},
        {"from": "in_progress", "to": "finished"},
        {"from": "finished", "to": "awaiting_validation"},
        {"from": "awaiting_validation", "to": "approved"},
    ],
    "permissions": {
        "Execution": ["in_progress", "finished"],
        "Coordenation": [],
        "Operational Management": ["approved"]
    }
}

STATUS_LABELS = {
    "open": "Aberta",
    "in_progress": "Em Execução",
    "paused": "Pausada",
    "finished": "Finalizada",
    "awaiting_validation": "Aguardando Validação",
    "approved": "Aprovada/Encerrada"
}


def get_workflow_for_tenant(tenant):
    try:
        return tenant.workflow.workflow_json
    except AttributeError:
        return DEFAULT_WORKFLOW
    except TenantWorkflow.DoesNotExist:
        return DEFAULT_WORKFLOW


def has_permission_for_status(user, target_status, workflow):
    user_level = user.technician.technician_level.name
    return target_status in workflow.get("permissions", {}).get(user_level, [])
