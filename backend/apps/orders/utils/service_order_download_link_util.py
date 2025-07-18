# backend.apps.orders.utils.service_order_donwload_link_util.py
import secrets
from backend.apps.orders.schemas import SERVICE_ORDER_DOWNLOAD_PURPOSE_SCHEMA

# Complementar quando o schema estiver composto
def get_purpose_rules(purpose: str):
    purpose_schema = SERVICE_ORDER_DOWNLOAD_PURPOSE_SCHEMA.get(purpose, {})
    purpose_rules = purpose_schema.get("purpose_rules",{})
    # life_time = purpose_rules.get("life_time")
    rules = {"...": ...}

    return rules

def generate_service_order_download_key(length: int = 16) -> str:
    "solidfield.co/os_download/..."
    return secrets.token_urlsafe(length)[:length]