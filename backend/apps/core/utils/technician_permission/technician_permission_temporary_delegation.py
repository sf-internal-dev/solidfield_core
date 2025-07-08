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

def can_delegate_action(granter, grantee, action_code: str) -> bool:
    granter_level = granter.technician_permission
    grantee_level = grantee.technician_permission

    # Verifica se delegação é permitida
    allowed_paths = {
        "L3": ["L2", "L1"],
        "L2": ["L1"],
    }

    if grantee_level not in allowed_paths.get(granter_level, []):
        return False

    # Busca todas as ações delegáveis incluindo herdadas
    delegable_actions = get_delegable_actions_deep(granter_level)

    return action_code in delegable_actions
