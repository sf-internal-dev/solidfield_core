# publisher.py
import json, uuid, time, hmac, hashlib, requests
from django.db import transaction
from django.conf import settings

GO_PUBLISH_URL = getattr(settings, "GO_PUBLISH_URL", "http://localhost:8080/publish")
SECRET = getattr(settings, "OUTBOUND_SIGNATURE_SECRET", b"...")

def _sign(b: bytes) -> str:
    return "sha256=" + hmac.new(SECRET, b, hashlib.sha256).hexdigest()

def _http_publish(body: bytes, timeout: float = 2.0):
    hdr = {
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
        "X-Signature": _sign(body),
    }
    return requests.post(GO_PUBLISH_URL, data=body, headers=hdr, timeout=timeout)

def get_client_ip(request):
    """
    Tenta extrair o IP real do client considerando proxies reversos.
    Atenção: upstream proxies devem setar X-Forwarded-For corretamente.
    """
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # X-Forwarded-For pode conter uma lista de IPs: client, proxy1, proxy2
        ip = xff.split(",")[0].strip()
        return ip
    # fallback
    return request.META.get("REMOTE_ADDR")


""" publish_ui_messages foi ajustada com objetivo de poder servir ao escopo de sessão
    quando não houver dados claros de quem é o tenant e technician"""
def publish_ui_messages(
    payloads: list[dict],
    *,
    actor_user_id: int | None = None,
    recipient_technician_id: int | None = None,
    recipient_user_id: int | None = None,
    recipient_session_id: str | None = None,
    tenant_id: int | None = None,
    client_ip: str | None = None,
    client_fingerprint: str | None = None,
    routing_candidates: list | None = None,
    source: str = "django_api",
):
    env = {
        "actor_user_id": actor_user_id,  
        # The ID of the user who initiated the action.
        # Used for auditing, logging, or displaying who caused the message.
        
        "recipient_technician_id": recipient_technician_id,  
        # The ID of the technician who should receive the message.
        # Direct delivery to a specific technician; if offline, message goes to pending/outbox.

        "recipient_user_id": recipient_user_id,  
        # The ID of the owner/manager user of the tenant.
        # Used as a fallback if the technician is not connected.
        # Can also be used for delivering messages only to the tenant owner.

        "recipient_session_id": recipient_session_id,  
        # The session ID or connection ID of the client that triggered the action.
        # Ensures immediate delivery only to that session, avoiding showing the message in all sessions of the owner.

        "tenant_id": tenant_id,  
        # The ID of the tenant related to the message.
        # Used for broadcasting messages to all active users or technicians in that tenant.

        "client_ip": client_ip,  
        # The IP address of the client that triggered the action.
        # Used as a fallback for message delivery when session or user IDs are not available.
        # Note: IP alone is not unique and may be shared across multiple clients.

        "client_fingerprint": client_fingerprint,  
        # Optional hash or token identifying the client device/session (e.g., hash of user-agent + nonce).
        # Helps disambiguate multiple connections from the same IP and prevent misdelivery.

        "correlation_id": str(uuid.uuid4()),  
        # A unique ID for the message used to track delivery and acknowledgments.
        # Useful for logging, debugging, and deduplicating messages.

        "idempotency_key": str(uuid.uuid4()),  
        # A unique key to guarantee idempotent delivery.
        # If a message is retried, the service recognizes it as the same message and avoids duplication.

        "source": source,  
        # A string identifying the source of the message (e.g., "django_api", "worker", etc.).
        # Useful for logging, debugging, or analytics.

        "messages": payloads,  
        # A list of message payloads (dictionaries) containing the actual content to be displayed.
        # Example payload: {"type": "error", "title": "Failure", "body": "Tenant could not be created."}

        "routing_candidates": routing_candidates or ["session","technician","tenant","owner","ip","pending"],
    }
    body = json.dumps(env, separators=(",", ":"), ensure_ascii=False).encode()

    def _send():
        for i in range(3):
            try:
                r = _http_publish(body)
                if r is not None and r.status_code < 500:
                    return
            except Exception:
                pass
            time.sleep(0.2 * (2 ** i))
    transaction.on_commit(_send)
    return env["correlation_id"]
