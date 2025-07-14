from core.schemas import ACTIONS_BY_PERMISSION_SCHEMA

# -> Checks if the technician has managerial level (L3)
def is_manager(technician) -> bool:
    return technician.technician_permission == "L3"
    
# -> Assigns a complete permission level to another technician
# Only allowed if the delegator has level L3
def delegate_complete_permission_level(delegator, delegate, target_level: str) -> bool:
    if is_manager(delegator):
        delegate.technician_permission = target_level
        delegate.save()
        return True
    return False

# -> Returns all effective actions available for a given permission level
# Supports deep selective inheritance defined in the schema
def get_effective_actions_for_level(level_key: str, visited=None) -> list[str]:
    if visited is None:
        visited = set()

    if level_key in visited:
        return []  

    visited.add(level_key)
    schema = ACTIONS_BY_PERMISSION_SCHEMA.get(level_key, {})
    effective_actions = {action["code"] for action in schema.get("actions", [])}

    inherited = schema.get("inherits_selectively_from", {})
    for inherited_level, actions in inherited.items():
        effective_actions.update(actions)
        effective_actions.update(get_effective_actions_for_level(inherited_level, visited))

    return list(effective_actions)

# -> Checks if the technician has access to a specific action code
def technician_has_permission_for_action(technician, action_code: str) -> bool:
    level = technician.technician_permission
    return action_code in get_effective_actions_for_level(level)

        