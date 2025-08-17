# backend.apps.orders.utils.service_order_donwload_link_util.py
import secrets
from backend.common.schemas.feedback_schemas import SERVICE_ORDER_DOWNLOAD_PURPOSE_SCHEMA

def validate_purpose_existance(purpose_schema: dict) -> bool:
    if purpose_schema == {}:
        return False
    return True

def get_purpose_rules(purpose: str) -> dict:
    purpose_schema = SERVICE_ORDER_DOWNLOAD_PURPOSE_SCHEMA.get(purpose, {})
    purpose_rules = purpose_schema.get("purpose_rules",{})
    if validate_purpose_existance(purpose_rules):
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

def generate_work_order_download_key(length: int = 14) -> str:
    "solidfield.co/os_download/..."
    return f"SODL{secrets.token_urlsafe(length)[:length]}"

