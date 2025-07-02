from backend.apps.core.workflow import DEFAULT_WORKFLOW

def get_workflow_for_tenant(tenant):
    """
    Returns the workflow JSON for a given tenant.
    If the tenant has no custom workflow, returns the default.
    """
    try:
        return tenant.status_workflow.workflow_json
    except tenant.status_workflow.workflow_json.DoesNotExist:
        return DEFAULT_WORKFLOW

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

def validate_transition(workflow: dict, from_status: str, to_status: str) -> bool:
    """
    Checks if a status transition is allowed based on the workflow.
    Returns True if a transition from `from_status` to `to_status` is defined.
    """
    transitions = workflow.get("transitions", [])
    return any(
        t.get("from") == from_status and t.get("to") == to_status for t in transitions
    )

def can_access_state(workflow: dict, role: str, state: str) -> bool:
    """
    Checks if a given role has access to a particular status.
    """
    return state in workflow.get("permissions", {}).get(role, [])

# Teste
if __name__ == "__main__":
    labels = generate_labels_for_workflow(DEFAULT_WORKFLOW)
    print("Labels gerados:")
    for key, label in labels.items():
        print(f"{key} → {label}")
