# publisher.py
import json, uuid, time, hmac, hashlib, requests
from django.db import transaction

PHOENIX_URL = "https://corex.your.app/api/oban/enqueue/ui_message"
SECRET = b"..."

def _sign(b: bytes) -> str:
    return "sha256=" + hmac.new(SECRET, b, hashlib.sha256).hexdigest()

def _post(body: bytes):
    hdr = {
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4()),
        "X-Signature": _sign(body),
    }
    return requests.post(PHOENIX_URL, data=body, headers=hdr, timeout=2.0)

def publish_ui_messages(technician_id:int, tenant_id:str, payloads:list[dict], source="django_api"):
    env = {
        "technician_id": technician_id,
        "tenant_id": tenant_id,
        "correlation_id": str(uuid.uuid4()),
        "source": source,
        "messages": payloads,
    }
    body = json.dumps(env, separators=(",", ":"), ensure_ascii=False).encode()

    def send_with_retry():
        for i in range(3):
            try:
                r = _post(body)
                if r.status_code < 500:
                    break
            except Exception:
                pass
            time.sleep(0.2 * (2 ** i))  # backoff: 200ms, 400ms, 800ms

    transaction.on_commit(send_with_retry)
