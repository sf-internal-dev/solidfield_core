from backend.apps.core.models import Technician, TemporaryDelegation
from backend.apps.orders.models import ServiceOrder, ServiceOrderDownloadLink
from backend.apps.checklist.models import Checklist, ChecklistTemplate, ChecklistItemTemplate, ChecklistItemAnswer
from backend.apps.filehub.models import ServiceOrderPhoto, ServiceOrderSignature
from backend.apps.clients.models import Client, ClientAddress, ClientFeedback, FeedbackLink
from backend.apps.core.schemas import AUDIT_LOG_ACTION_SCHEMA
from backend.apps.core.utils.audition_log.audition_log_util import log_audit_action
from django.utils import timezone


""" Permission Delegation """
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

""" Service Order """
# -> Logs the creation of a service order
# Includes order identifier and creation date
def log_service_order_creation(service_order: ServiceOrder):
    log_audit_action(
        technician=service_order.created_by,
        action="service_order_creation",
        object_instance=service_order,
        data={
            "order_id": service_order.identifier,
            "timestamp": timezone.now().isoformat(),
        }
    )

# -> Logs the first assignment of a service order to a technician
# Includes order identifier assigned technician
def log_service_order_assignment(service_order: ServiceOrder, technician: Technician):
    log_audit_action(
        technician=service_order.created_by,
        action="service_order_assignment",
        object_instance=service_order,
        data={
            "order_id": service_order.identifier,
            "assigned_technician":technician,
        }
    )

# -> Logs the reassignment of a service order to a new technician
# Includes order identifier, old and new technician assigned
def log_service_order_reassignment(service_order: ServiceOrder, current_technician: Technician, new_technician):
    log_audit_action(
        technician=service_order.created_by,
        action="service_order_reassignment",
        object_instance=service_order,
        data={
            "order_id": service_order.identifier,
            "old_technician":current_technician,
            "new_technician":new_technician,
        }
    )

# -> Logs the management-level validation of a finalizes service order
# Includes order identified and validation date
def log_service_order_validation(service_order: ServiceOrder):
    log_audit_action(
        technician=service_order.created_by,
        action="service_order_validation",
        object_instance=service_order,
        data={
            "order_id": service_order.identifier,
            "timestamp": timezone.now().isoformat(),
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

""" Service Order Download Link """
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

""" Service Order Files """

# -> Logs the upload of a audit photo to a service order
# Includes order identifier and act timestamp
def log_service_order_photo_upload(service_order_photo: ServiceOrderPhoto):
    log_audit_action(
        technician=service_order_photo.service_order.from_user,
        action="service_order_pdf_generation",
        object_instance=service_order_photo,
        data={
            "order_id": service_order_photo.service_order.identifier,
            "timestamp": timezone.now().isoformat(),
        }
    )

# -> Logs the upload of a client signature to a service order
# Includes order identifier, client name and act timestamp
def log_service_order_client_signature_upload(service_order_signature: ServiceOrderSignature, client_name: str):
    log_audit_action(
        technician=service_order_signature.service_order.from_user,
        action="service_order_pdf_generation",
        object_instance=service_order_signature,
        data={
            "order_id": service_order_signature.service_order.identifier,
            "timestamp": timezone.now().isoformat(),
            "client_name":client_name,
        }   
    )
    
""" Client Feedback """
# -> Logs the generation of a feedback request link
# Includes order identifier
def log_feedback_request_generation(client_feedback_link: FeedbackLink):
    log_audit_action(
        technician=client_feedback_link.service_order.technician,
        action="feedback_request_generation",
        object_instance=client_feedback_link,
        data = {
            "order_id": client_feedback_link.service_order.identifier,
        }
    )

# -> Logs the feedback received for a service execution
# Includes order identifier
def log_service_order_feedback_received(client_feedback: ClientFeedback):
     log_audit_action(
        technician=client_feedback.service_order.technician,
        action="service_order_feedback_received",
        object_instance=client_feedback,
        data = {
            "order_id": client_feedback.service_order.identifier,
        }
    )
    

""" Offline Sync"""
# -> Logs the offline sync event of a technician
# Includes timestamp and items synced
# sync_event to define as model
def log_offline_sync_event(sync_event: str, items_synced: list):
    log_audit_action(
        technician=sync_event.technician,
        action="offline_sync_event",
        object_instance=sync_event,
        data = {
            "timestamp": timezone.now().isoformat(),
            items_synced: items_synced
        }
    )


""" Checklist & Template """
# -> Logs the checklist submission to a service order
# Includes timestamp
def log_checklist_submission(checklist: Checklist):
    log_audit_action(
        technician=checklist.template.service_order.technician,
        action="checklist_submission",
        object_instance=checklist,
        data = {
            "timestamp": timezone.now().isoformat(),
        }
    )

# -> Logs the update of a template version
# Includes template name and version
def log_template_version_update(checklist_template: ChecklistTemplate):
    log_audit_action(
        technician=checklist_template.service_order.technician,
        action="template_version_update",
        object_instance=checklist_template,
        data = {
            "template_name": checklist_template.name,
            "version": checklist_template.version
        }
    )

""" Technician Tracking """

# -> Logs the login event of a technician
# Includes timestamp
def log_login_event(technician: Technician):
    log_audit_action(
        technician=technician,
        action="login_event",
        object_instance=technician,
        data = {
            "timestamp": timezone.now().isoformat(),
        }
    )

# -> Logs the assignment of technicians for a operational aggroupment
# Includes technicians assigned and operational aggroupment name
def log_group_assignment(technician: Technician, technicians: list, group_name: str):
    log_audit_action(
        technician=technician,
        action="group_assignment",
        object_instance=technician,
        data = {
            technicians: technicians,
            group_name: group_name,
        }
    )
