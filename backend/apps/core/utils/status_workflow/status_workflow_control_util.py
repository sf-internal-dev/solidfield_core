from .status_workflow_label_util import generate_labels_for_workflow
from backend.apps.core.workflow import DEFAULT_STATUS_WORKFLOW

# -> Validates if a status transition is allowed in the given workflow
# Returns True only if a defined transition from `from_status` to `to_status` exists
def validate_transition(workflow: dict, from_status: str, to_status: str) -> bool:
    """
    Checks if a status transition is allowed based on the workflow.
    Returns True if a transition from `from_status` to `to_status` is defined.
    """
    transitions = workflow.get("transitions", [])
    return any(
        t.get("from") == from_status and t.get("to") == to_status for t in transitions
    )

# -> Checks if a given role (permission level) has access to a specific status/state
# Useful for enforcing permission-based workflow constraints
def can_access_state(workflow: dict, role: str, state: str) -> bool:
    """
    Checks if a given role has access to a particular status.
    """
    return state in workflow.get("permissions", {}).get(role, [])

# Teste
if __name__ == "__main__":
    labels = generate_labels_for_workflow(DEFAULT_STATUS_WORKFLOW)
    print("Labels gerados:")
    for key, label in labels.items():
        print(f"{key} → {label}")
