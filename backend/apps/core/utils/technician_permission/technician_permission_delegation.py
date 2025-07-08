from core.schemas import ACTIONS_BY_PERMISSION_SCHEMA

# Confirma que o Technician tem L3 pra fazer a delegação
def is_manager(technician) -> bool:
    return technician.technician_permission == "L3"
    
# Faz a delegação completa de nível de permissão a um técnico
def delegate_complete_permission_level(granter, grantee, target_level: str) -> bool:
    if is_manager(granter):
        grantee.technician_permission = target_level
        grantee.save()
        return True
    return False

def get_effective_actions_for_level(level_key: str, visited=None) -> list[str]:
    if visited is None:
        visited = set()

    if level_key in visited:
        return []  # Evita recursão infinita por erro de configuração

    visited.add(level_key)
    schema = ACTIONS_BY_PERMISSION_SCHEMA.get(level_key, {})
    effective_actions = {action["code"] for action in schema.get("actions", [])}

    inherited = schema.get("inherits_selectively_from", {})
    for inherited_level, actions in inherited.items():
        effective_actions.update(actions)
        # Inclui também as ações herdadas do nível herdado
        # (respeitando o modelo de herança seletiva profunda)
        effective_actions.update(get_effective_actions_for_level(inherited_level, visited))

    return list(effective_actions)

def technician_has_permission_for_action(technician, action_code: str) -> bool:
    level = technician.technician_permission
    return action_code in get_effective_actions_for_level(level)

        