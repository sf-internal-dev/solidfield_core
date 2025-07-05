from backend.apps.core.workflow import DEFAULT_STATUS_WORKFLOW

def get_workflow_for_tenant(tenant):
    """
    Returns the workflow JSON for a given tenant.
    If the tenant has no custom workflow, returns the default.
    """
    try:
        return tenant.status_workflow.workflow_json
    except tenant.status_workflow.workflow_json.DoesNotExist:
        return DEFAULT_STATUS_WORKFLOW

def get_workflow_status_label(status: str) -> str:
    """
    Converts a snake_case status to a human-readable label.
    Example: "in_progress" -> "In Progress"
    """
    return ' '.join(part.capitalize() for part in status.split('_'))

def generate_labels_for_workflow(workflow: dict) -> dict:
    """
    Generates readable labels for all states in the workflow.
    Returns a dict mapping each state to its formatted label.
    """
    return {state: get_workflow_status_label(state) for state in workflow.get("states", [])}