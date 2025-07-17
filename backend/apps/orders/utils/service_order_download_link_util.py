# backend.apps.orders.utils.service_order_donwload_link_util.py
import secrets

def generate_service_order_download_key(length: int = 16):
    "solidfield.co/os_download/..."
    return secrets.token_urlsafe(length)[:length]