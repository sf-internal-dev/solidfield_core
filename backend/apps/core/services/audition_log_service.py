from backend.apps.core.models import Technician, TemporaryDelegation
from backend.apps.orders.models import ServiceOrder, ServiceOrderDownloadLink
from backend.apps.core.schemas import AUDIT_LOG_ACTION_SCHEMA
from backend.apps.core.utils.audition_log.audition_log_util import log_audit_action
from django.utils import timezone

# -> Logs a permission level delegation from one technician to another
# Includes context with usernames and assigned permission level
def log_permission_level_delegation(delegator: Technician, delegate: Technician, permission_level: str):
    return log_audit_action(
        technician=delegator,
        action_code="permission_level_delegation",
        object_instance=delegate,
        context_data={
            "permission_level": permission_level,
            "delegate_user": delegate.username,
            "delegator_user": delegator.username,
        }
    )

# -> Logs a temporary delegation of actions from one technician to another
# Includes validity period and list of delegated actions in the context
def log_temporary_delegation(delegation: TemporaryDelegation, actions: list[str]):
    return log_audit_action(
        technician=delegation.from_user,
        action_code="temporary_delegation",
        object_instance=delegation,
        context_data={
            "delegate_user": delegation.to_user.username,
            "delegator_user": delegation.from_user.username,
            "valid_from": delegation.valid_from.isoformat(),
            "valid_until": delegation.valid_until.isoformat(),
            "actions_delegated": ", ".join(actions),
        }
    )

# -> Logs a service order status transition
# Includes previous and new status in the audit context
def log_service_order_status_transition(service_order: ServiceOrder, new_status: str):
    return log_audit_action(
        technician=service_order.technician,
        action="status_transition",
        object_instance=service_order,
        data={
            "order_id": service_order.identifier,
            "from": service_order.status, 
            "to": new_status
        }
    )

# -> Logs the revocation of a temporary delegation
# Includes the affected user and timestamp of revocation
def log_revoke_temporary_delegation(delegation: TemporaryDelegation):
    log_audit_action(
        technician=delegation.from_user,
        action="revoke_delegation",
        object_instance=delegation,
        data={
            "delegate_user": delegation.to_user.username,
            "revoked_at": timezone.now().isoformat()
        }
    )

# -> Logs the creation of a service order
# Includes assigned technician and creation date
def log_service_order_creation(service_order: ServiceOrder):
    log_audit_action(
        technician=service_order.created_by,
        action="service_order_creation",
        object_instance=service_order,
        data={
            "order_id": service_order.identifier,
            "creation_date": timezone.now().isoformat(),
        }
    )

# -> Logs the creation of a service order
# Includes order id, download link key and generation purpose
def log_service_order_download_link_creation(service_order_download_link: ServiceOrderDownloadLink):
    log_audit_action(
        technician=service_order_download_link.service_order.from_user,
        action="service_order_download_link_creation",
        object_instance=service_order_download_link,
        data={
            "order_id": service_order_download_link.service_order.identifier,
            "key":service_order_download_link.key,
            "purpose":service_order_download_link.purpose
        }
    )

# -> Logs the creation of a service order
# Includes download link key for pdf generation
def log_service_order_pdf_generation(service_order_download_link: ServiceOrderDownloadLink):
    log_audit_action(
        technician=service_order_download_link.service_order.from_user,
        action="service_order_pdf_generation",
        object_instance=service_order_download_link,
        data={
            "key":service_order_download_link.key,
        }
    )