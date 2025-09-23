from backend.apps.core.models import Technician, TemporaryDelegation
from backend.apps.orders.models import WorkOrder, WorkOrderDownloadLink
from backend.apps.checklist.models import Checklist, ChecklistTemplate, ChecklistItemTemplate, ChecklistItemAnswer
from backend.apps.filehub.models import WorkOrderPhoto, WorkOrderSignature
from backend.apps.clients.models import Client, ClientAddress, ClientFeedback, FeedbackLink
from backend.common.schemas.audition_log_schemas import AUDIT_LOG_ACTION_SCHEMA
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

""" Work Order """
# -> Logs the creation of a Work order
# Includes order identifier and creation date
def log_work_order_creation(work_order: WorkOrder):
    log_audit_action(
        technician=work_order.created_by,
        action="work_order_creation",
        object_instance=work_order,
        data={
            "order_id": work_order.identifier,
            "timestamp": timezone.now().isoformat(),
        }
    )

# -> Logs the first assignment of a Work order to a technician
# Includes order identifier assigned technician
def log_work_order_assignment(work_order: WorkOrder, technician: Technician):
    log_audit_action(
        technician=work_order.created_by,
        action="work_order_assignment",
        object_instance=work_order,
        data={
            "order_id": work_order.identifier,
            "assigned_technician":technician,
        }
    )

# -> Logs the reassignment of a Work order to a new technician
# Includes order identifier, old and new technician assigned
def log_work_order_reassignment(work_order: WorkOrder, current_technician: Technician, new_technician):
    log_audit_action(
        technician=work_order.created_by,
        action="work_order_reassignment",
        object_instance=work_order,
        data={
            "order_id": work_order.identifier,
            "old_technician":current_technician,
            "new_technician":new_technician,
        }
    )

# -> Logs the management-level validation of a finalizes Work order
# Includes order identified and validation date
def log_work_order_validation(work_order: WorkOrder):
    log_audit_action(
        technician=work_order.created_by,
        action="work_order_validation",
        object_instance=work_order,
        data={
            "order_id": work_order.identifier,
            "timestamp": timezone.now().isoformat(),
        }
    )


# -> Logs a Work order status transition
# Includes previous and new status in the audit context
def log_work_order_status_transition(work_order: WorkOrder, new_status: str):
    return log_audit_action(
        technician=work_order.technician,
        action="status_transition",
        object_instance=work_order,
        data={
            "order_id": work_order.identifier,
            "from": work_order.status, 
            "to": new_status
        }
    )

""" Work Order Download Link """
# -> Logs the creation of a Work order
# Includes order id, download link key and generation purpose
def log_work_order_download_link_creation(work_order_download_link: WorkOrderDownloadLink):
    log_audit_action(
        technician=work_order_download_link.work_order.from_user,
        action="work_order_download_link_creation",
        object_instance=work_order_download_link,
        data={
            "order_id": work_order_download_link.work_order.identifier,
            "key":work_order_download_link.key,
            "purpose":work_order_download_link.purpose
        }
    )

# -> Logs the creation of a Work order
# Includes download link key for pdf generation
def log_work_order_pdf_generation(work_order_download_link: WorkOrderDownloadLink):
    log_audit_action(
        technician=work_order_download_link.work_order.from_user,
        action="work_order_pdf_generation",
        object_instance=work_order_download_link,
        data={
            "key":work_order_download_link.key,
        }
    )

""" Work Order Files """

# -> Logs the upload of a audit photo to a Work order
# Includes order identifier and act timestamp
def log_work_order_photo_upload(work_order_photo: WorkOrderPhoto):
    log_audit_action(
        technician=work_order_photo.work_order.from_user,
        action="work_order_pdf_generation",
        object_instance=work_order_photo,
        data={
            "order_id": work_order_photo.work_order.identifier,
            "timestamp": timezone.now().isoformat(),
        }
    )

# -> Logs the upload of a client signature to a Work order
# Includes order identifier, client name and act timestamp
def log_work_order_client_signature_upload(work_order_signature: WorkOrderSignature, client_name: str):
    log_audit_action(
        technician=work_order_signature.work_order.from_user,
        action="work_order_pdf_generation",
        object_instance=work_order_signature,
        data={
            "order_id": work_order_signature.work_order.identifier,
            "timestamp": timezone.now().isoformat(),
            "client_name":client_name,
        }   
    )
    
""" Client Feedback """
# -> Logs the generation of a feedback request link
# Includes order identifier
def log_feedback_request_generation(client_feedback_link: FeedbackLink):
    log_audit_action(
        technician=client_feedback_link.work_order.technician,
        action="feedback_request_generation",
        object_instance=client_feedback_link,
        data = {
            "order_id": client_feedback_link.work_order.identifier,
        }
    )

# -> Logs the feedback received for a Work execution
# Includes order identifier
def log_work_order_feedback_received(client_feedback: ClientFeedback, feedback_label: str):
     log_audit_action(
        technician=client_feedback.work_order.technician,
        action="work_order_feedback_received",
        object_instance=client_feedback,
        data = {
            "order_id": client_feedback.work_order.identifier,
            "feedback_label": feedback_label,
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
# -> Logs the checklist submission to a Work order
# Includes timestamp
def log_checklist_submission(checklist: Checklist):
    log_audit_action(
        technician=checklist.template.work_order.technician,
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
        technician=checklist_template.work_order.technician,
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
def log_group_assignment(technician: Technician, technicians: list, aggroupment_tag: str,*, aggroupment=None):
    obj = aggroupment if aggroupment is not None else technician
    log_audit_action(
        technician=technician,
        action_code="aggroupment_assignment",
        object_instance=obj,
        context_data = {
            "technician":getattr(technician, "username", str(technician)),
            "technicians": technicians,
            "aggroupment_tag": aggroupment_tag,
        }
    )
