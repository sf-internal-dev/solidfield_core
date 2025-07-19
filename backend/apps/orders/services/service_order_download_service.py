from backend.apps.orders.utils.service_order_download_link_util import generate_service_order_download_key, get_purpose_rules
from backend.apps.orders.models.service_order import ServiceOrderDownloadLink, ServiceOrder
from backend.apps.core.models.technician import Technician
from datetime import datetime,timedelta


def create_service_order_download_link_with_key(service_order: ServiceOrder, technician: Technician, purpose: str):
    download_key = generate_service_order_download_key()
    return ServiceOrderDownloadLink.objects.create(
        service_order = service_order,
        key = download_key,
        technician = technician,
        created_at = datetime.now(),
        purpose = purpose,
    )

def calculate_defined_download_link_life_time(service_order_download_link: ServiceOrderDownloadLink, days: int):
    created_at = service_order_download_link.created_at
    expires_at = created_at + timedelta(days)
    service_order_download_link.expires_at = expires_at

def get_purpose_rules_for_service_order_download_link(service_order_download_link: ServiceOrderDownloadLink):
    purpose = service_order_download_link.purpose
    purpose_rules = get_purpose_rules(purpose)


    

