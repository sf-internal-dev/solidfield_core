import secrets

def generate_feedback_request_key(length: int = 14) -> str:
    return f"FRL{secrets.token_urlsafe(length)[:length]}"

def feedback_request_link(base_url: str, key_length: int = 14) -> str:
    return f"{base_url.rstrip('/')}/feedback/{generate_feedback_request_key(key_length)}"
