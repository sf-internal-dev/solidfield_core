from backend.common.schemas.permission_schemas import ACTIONS_BY_PERMISSION_SCHEMA
from typing import Optional
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

def get_effective_action_objects_for_level(level_key: str, visited=None) -> list[dict]:

    if visited is None:
        visited = set()

    if level_key in visited:
        return []

    visited.add(level_key)
    schema = ACTIONS_BY_PERMISSION_SCHEMA.get(level_key, {})
    
    # ações próprias do nível
    effective_actions: dict[str, dict] = {
        action["code"]: action for action in schema.get("actions", [])
    }

    # heranças seletivas
    inherited = schema.get("inherits_selectively_from", {})
    for inherited_level, actions in inherited.items():
        inherited_effective = get_effective_action_objects_for_level(inherited_level, visited)
        
        for action in inherited_effective:
            if action["code"] in actions:  # só herda se o código está listado
                effective_actions.setdefault(action["code"], action)

    return list(effective_actions.values())

def get_action_label(level_key: str, action_code: str) -> Optional[str]:
    actions = get_effective_action_objects_for_level(level_key)
    for action in actions:
        if action["code"] == action_code:
            return action["label"]
    return None

# -> Checks if the technician has access to a specific action code
def technician_has_permission_for_action(technician, action_code: str) -> bool:
    level = technician.technician_permission
    return action_code in get_effective_actions_for_level(level)

        