from backend.common.schemas.permission_schemas import ACTIONS_BY_PERMISSION_SCHEMA

# -> Recursively returns all actions marked as delegable for a given permission level
# Includes inherited actions defined in the selective inheritance schema
def get_delegable_actions_deep(level_key: str) -> list[str]:
    visited = set()

    def collect(level):
        if level in visited:
            return []
        visited.add(level)

        actions = ACTIONS_BY_PERMISSION_SCHEMA.get(level, {}).get("actions", [])
        delegable = [a["code"] for a in actions if a.get("delegable")]

        inherited = ACTIONS_BY_PERMISSION_SCHEMA.get(level, {}).get("inherits_selectively_from", {})
        for inherited_level in inherited.keys():
            delegable += collect(inherited_level)
        return delegable

    return list(set(collect(level_key)))

# -> Checks if a delegator can delegate a specific action to a target technician
# Only allowed if the target level is permitted and the action is marked as delegable
def can_delegate_action(delegator, delegate, action_code: str) -> bool:
    delegator_level = delegator.technician_permission
    delegate_level = delegate.technician_permission

    allowed_paths = {
        "L3": ["L2", "L1"],
        "L2": ["L1"],
    }

    if delegate_level not in allowed_paths.get(delegator_level, []):
        return False

    delegable_actions = get_delegable_actions_deep(delegator_level)

    return action_code in delegable_actions
