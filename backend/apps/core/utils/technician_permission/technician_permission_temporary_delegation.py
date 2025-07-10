from core.schemas import ACTIONS_BY_PERMISSION_SCHEMA

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
