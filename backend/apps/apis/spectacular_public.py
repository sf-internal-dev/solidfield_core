"""
Tags e fragmentos de schema reutilizáveis para o pacote **Public API v1 — Field operations**.

Ver também: `API_PUBLIC_CONTRACT.md` na raiz do repositório (política de estabilidade e lista de endpoints).
"""

TAG_OFFLINE = "Public v1 — Offline sync"
TAG_CHECKLIST = "Public v1 — Checklist"
TAG_WORK_ORDER = "Public v1 — Work orders"


def schema_error_422():
    return {
        "type": "object",
        "properties": {
            "codes": {"type": "array", "items": {"type": "string"}},
            "correlation_id": {"type": "string", "nullable": True},
        },
    }


def schema_error_401():
    return {
        "type": "object",
        "properties": {
            "codes": {"type": "array", "items": {"type": "string"}},
            "correlation_id": {"type": "string", "nullable": True},
        },
    }
