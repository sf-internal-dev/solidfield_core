# backend.apps.orders.utils.service_order_donwload_link_util.py
import secrets
from backend.apps.orders.schemas import SERVICE_ORDER_DOWNLOAD_PURPOSE_SCHEMA

def get_purpose_rules(purpose: str):
    purpose_schema = SERVICE_ORDER_DOWNLOAD_PURPOSE_SCHEMA.get(purpose, {})
    purpose_rules = purpose_schema.get("purpose_rules",{})
    rules = {
        "client_as_first": purpose_rules.get("client_as_first"),
        "available_to_client": purpose_rules.get("available_to_client"),
        "access_level_required": purpose_rules.get("access_level_required"),
        "include_technician_notes": purpose_rules.get("include_technician_notes"),
        "include_signature": purpose_rules.get("include_signature"),
        "include_checklist": purpose_rules.get("include_checklist"),
        "offline_friendly": purpose_rules.get("offline_friendly"),
             }

    return rules

def generate_service_order_download_key(length: int = 16) -> str:
    "solidfield.co/os_download/..."
    return secrets.token_urlsafe(length)[:length]