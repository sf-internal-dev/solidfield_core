from .status_workflow_label_util import generate_labels_for_workflow
from backend.common.work_order_status_workflow import DEFAULT_STATUS_WORKFLOW
from typing import Set

def has_required_keys(workflow, required_keys):
    if not isinstance(workflow, dict):
        return False, ["Workflow must be a dictionary."]
    missing = required_keys - workflow.keys()
    return len(missing) == 0, [f"Missing required keys: {', '.join(missing)}."] if missing else []

def validate_states(states):
    if not isinstance(states, list) or not states or not all(isinstance(s, str) for s in states):
        return False, ["'states' must be a non-empty list of strings."]
    return True, []

def validate_transitions(transitions, declared_states):
    errors = []
    if not isinstance(transitions, list) or not transitions:
        return False, ["'transitions' must be a non-empty list."]
    for t in transitions:
        if not isinstance(t, dict) or "from" not in t or "to" not in t:
            errors.append("Each transition must be a dict with 'from' and 'to'.")
            continue
        if t["from"] not in declared_states or t["to"] not in declared_states:
            errors.append(f"Invalid transition: '{t.get('from')}' → '{t.get('to')}' not in 'states'.")
    return len(errors) == 0, errors

def validate_single_terminal(declared_states, transitions):
    froms = {t["from"] for t in transitions if isinstance(t, dict) and "from" in t}
    terminals = [s for s in declared_states if s not in froms]
    if len(terminals) != 1:
        return False, [f"Workflow must have exactly 1 terminal state, found {terminals or 'none'}."]
    return True, []

def validate_permissions(permissions, declared_states):
    errors = []
    if not isinstance(permissions, dict):
        return False, ["'permissions' must be a dictionary."]
    for role, allowed_states in permissions.items():
        if not isinstance(role, str):
            errors.append(f"Invalid permission key: {role} (must be string).")
            continue
        if not isinstance(allowed_states, list) or not all(isinstance(s, str) for s in allowed_states):
            errors.append(f"Permissions for '{role}' must be a list of strings.")
            continue
        invalid_states = [s for s in allowed_states if s not in declared_states]
        if invalid_states:
            errors.append(f"Permissions for '{role}' reference invalid states: {invalid_states}.")
    return len(errors) == 0, errors

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

# -> Returns the last state of a workflow, be it the default or customized for the tenant
# Useful for terminal actions like validating and finalizing a work order
def get_terminal_state(workflow: dict) -> str:
    transitions = workflow.get("transitions", [])
    declared_states: Set[str] = set(workflow.get("states") or [])
    froms = {t.get("from") for t in transitions if t.get("from")}

    terminal = [s for s in declared_states if s not in froms]

    return terminal[0]
    

# -> Checks if a given role (permission level) has access to a specific status/state
# Useful for enforcing permission-based workflow constraints
def can_access_state(workflow: dict, role: str, state: str) -> bool:
    """
    Checks if a given role has access to a particular status.
    """
    return state in workflow.get("permissions", {}).get(role, [])

# Test
if __name__ == "__main__":
    labels = generate_labels_for_workflow(DEFAULT_STATUS_WORKFLOW)
    print("Generated labels:")
    for key, label in labels.items():
        print(f"{key} → {label}")
