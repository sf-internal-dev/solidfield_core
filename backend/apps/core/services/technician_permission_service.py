from backend.apps.core.utils.technician_permission.technician_permission_delegation_util import get_effective_actions_for_level,technician_has_permission_for_action, get_action_label
from backend.apps.core.utils.technician_permission.technician_permission_temporary_delegation_util import can_delegate_action
from backend.apps.core.utils.audition_log.audition_log_util import log_audit_action
from backend.apps.core.models import Technician, TemporaryDelegation, DelegatedAction
from backend.apps.core.services.audition_log_service import log_permission_level_delegation, log_temporary_delegation, log_revoke_temporary_delegation

from backend.apps.core.models.log import AuditLog
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import transaction
from typing import Tuple, List

# -> Delegates a permission level from a level 3 technician (L3) to another technician
# Only L3 can assign levels; persists the change and logs the action
def delegate_permission_level(delegator: Technician, delegate: Technician, level: str)-> Tuple[bool, List[str]]:
    if delegator.technician_permission != "L3":
        return False, ["delegator_not_manager"]
    delegate.technician_permission = level
    delegate.save(update_fields=["technician_permission"])
    log_permission_level_delegation(delegator, delegate, level)
    return True, []

# -> Creates a temporary delegation of specific actions from one technician to another
# Validates each action, persists the delegation and logs the event
# Fails if technician attempts to delegate to themselves or invalid actions
@transaction.atomic
def create_temporary_delegation(from_user, to_user, actions: list[str], valid_from, valid_until):
    errors: List[str] = []

    if from_user == to_user:
        return None, errors.append("tried_to_delegate_to_itself")
    
    delegation = TemporaryDelegation.objects.create(
        from_user=from_user,
        to_user=to_user,
        valid_from=valid_from,
        valid_until=valid_until,
        tenant=from_user.tenant
    )

    valid_actions = []
    for action in actions:
        if can_delegate_action(from_user, to_user, action):
            valid_actions.append(
                DelegatedAction(delegation=delegation, action=action)
            )
        else:
            return None, errors.append(f"invalid_action: {action}")

    if not valid_actions:
        errors.insert(0, "no_valid_actions")
        return None, errors

    for da in valid_actions:
        da.delegation = delegation
    DelegatedAction.objects.bulk_create(valid_actions)

    log_temporary_delegation(delegation,actions)

    return delegation, errors

# -> Checks if a technician has permission for a specific action
# Returns True if permission is granted by level or via active delegation
def has_permission(technician: Technician, action_code: str) -> Tuple[bool, str]:
    label = get_action_label(level_key=technician.technician_permission, action_code=action_code)

    if technician_has_permission_for_action(technician, action_code):
        return True, ""
    
    elif not technician_has_permission_for_action(technician, action_code):
        now = timezone.now()
        return TemporaryDelegation.objects.filter(
            to_user=technician,
            valid_from__lte=now,
            valid_until__gte=now,
            actions__action=action_code
        ).exists(), ""
    return False, f"technician_has_no_permission:{label}"

# -> Lists all effective actions currently available to a technician
# Includes both native permission level and active delegated actions
def list_effective_permissions(technician: Technician) -> list[str]:
    actions = set(get_effective_actions_for_level(technician.technician_permission))

    now = timezone.now()
    delegated = DelegatedAction.objects.filter(
        delegation__to_user=technician,
        delegation__valid_from__lte=now,
        delegation__valid_until__gte=now,
    ).values_list("action", flat=True)

    actions.update(delegated)
    return list(actions)

# -> Revokes a temporary delegation and logs the action
def revoke_delegation(delegation: TemporaryDelegation):
    log_revoke_temporary_delegation(delegation)
    delegation.delete()

# -> Returns all delegations created by the technician
# Ordered by expiration date descending
def list_outgoing_delegations(technician: Technician):
    return TemporaryDelegation.objects.filter(from_user=technician).order_by("-valid_until")

# -> Returns all delegations received by the technician
# Ordered by expiration date descending
def list_incoming_delegations(technician: Technician):
    return TemporaryDelegation.objects.filter(to_user=technician).order_by("-valid_until")

