from backend.apps.core.utils.technician_permission.technician_permission_delegation import get_effective_actions_for_level,technician_has_permission_for_action
from backend.apps.core.utils.technician_permission.technician_permission_temporary_delegation import technician_has_permission_for_action, can_delegate_action
from backend.apps.core.utils.audition_log.audition_log_util import log_audit_action
from backend.apps.core.models import Technician, TemporaryDelegation, DelegatedAction
from core.models.log import AuditLog
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import transaction

def delegate_permission_level(delegator: Technician, delegate: Technician, level: str) -> bool:
    if delegator.technician_permission != "L3":
        return False
    delegate.technician_permission = level
    delegate.save()
    log_audit_action(
        technician=delegator,
        action="delegate_permission_level",
        object_instance=Technician,
        data={
            "permission_level": level,
            "delegate_user": delegate.username,
            "delegator_user": delegator.username,
        }
    )
    return True

@transaction.atomic
def create_temporary_delegation(from_user, to_user, actions: list[str], valid_from, valid_until):
    if from_user == to_user:
        raise ValueError("Cannot delegate to oneself.")
    
    delegation = TemporaryDelegation.objects.create(
        from_user=from_user,
        to_user=to_user,
        valid_from=valid_from,
        valid_until=valid_until,
        tenant=from_user.tenant
    )

    valid_actions = []
    for action in actions:
        if can_delegate_action(from_user, action, to_user):
            valid_actions.append(
                DelegatedAction(delegation=delegation, action=action)
            )
        else:
            raise ValueError(f"Action '{action}' cannot be delegated from {from_user} to {to_user}.")

    DelegatedAction.objects.bulk_create(valid_actions)

    log_audit_action(
        technician=delegation.from_user,
        action="delegate_temporary_permissions",
        object_instance=TemporaryDelegation,
        data={
            "delegator_user": delegation.from_user.username,
            "delegate_user": delegation.to_user.username,
            "actions_delegated": actions,
            "valid_from": delegation.valid_from.isoformat(),
            "valid_until": delegation.valid_until.isoformat(),
        }
    )

    return delegation

def has_permission(technician: Technician, action_code: str) -> bool:
    if technician_has_permission_for_action(technician, action_code):
        return True

    now = timezone.now()
    return TemporaryDelegation.objects.filter(
        to_user=technician,
        valid_from__lte=now,
        valid_until__gte=now,
        actions__action=action_code
    ).exists()

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

def revoke_delegation(delegation: TemporaryDelegation):
    log_audit_action(
        technician=delegation.from_user,
        action="revoke_delegation",
        object_instance=delegation,
        data={
            "delegate_user": delegation.to_user.username,
            "revoked_at": timezone.now().isoformat()
        }
    )
    delegation.delete()

def list_outgoing_delegations(technician: Technician):
    return TemporaryDelegation.objects.filter(from_user=technician).order_by("-valid_until")

def list_incoming_delegations(technician: Technician):
    return TemporaryDelegation.objects.filter(to_user=technician).order_by("-valid_until")

