import secrets

def generate_feedback_request_key(length: int = 14) -> str:
    "solidfield.co/os_download/..."
    return f"FRL{secrets.token_urlsafe(length)[:length]}"
