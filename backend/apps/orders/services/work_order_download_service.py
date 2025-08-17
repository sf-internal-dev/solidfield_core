from backend.apps.orders.utils.work_order_download_link_util import generate_work_order_download_key, get_purpose_rules
from backend.apps.orders.models.work_order import WorkOrderDownloadLink, WorkOrder
from backend.apps.core.models.technician import Technician
from backend.apps.core.services.audition_log_service import log_work_order_download_link_creation
from datetime import datetime,timedelta



def calculate_defined_download_link_life_time(work_order_download_link: WorkOrderDownloadLink, days: int):
    created_at = work_order_download_link.created_at
    expires_at = created_at + timedelta(days)
    timestamp = work_order_download_link.expires_at = expires_at
    return timestamp

# Função deve retornar valores com propósito de enviar-los para leitura pelo corex
def get_purpose_rules_for_work_order_download_link(work_order_download_link: WorkOrderDownloadLink):
    purpose = work_order_download_link.purpose
    purpose_rules = get_purpose_rules(purpose)
    return purpose_rules
    
def create_work_order_download_link_with_key(work_order: WorkOrder, technician: Technician, purpose: str):
    download_key = generate_work_order_download_key()
    work_order_download_link = WorkOrderDownloadLink.objects.create(
        work_order = work_order,
        key = download_key,
        technician = technician,
        created_at = datetime.now(),
    )
    
    purpose_rules = get_purpose_rules_for_work_order_download_link(work_order_download_link)
    if purpose not in purpose_rules:
        work_order_download_link.purpose = None
        work_order_download_link.save(update_fields=["purpose"])

    log_work_order_download_link_creation(work_order_download_link)

    return work_order_download_link