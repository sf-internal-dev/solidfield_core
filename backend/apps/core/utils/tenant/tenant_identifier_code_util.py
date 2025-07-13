import re
from django.utils.crypto import get_random_string
from django.utils.text import slugify
import unicodedata

def generate_tenant_code_attempts(slug: str, max_tries: int = 30) -> list[str]:
    normalized = unicodedata.normalize("NFKD", slug)
    ascii_slug = normalized.encode("ascii", "ignore").decode("ascii")
    base = re.sub(r'[^A-Z0-9]', '', ascii_slug.upper())[:4] or "COMP"
    base = base[:4]

    attempts = []
    for i in range(max_tries):
        suffix = "" if i == 0 else str(i)
        attempt = f"{base}{suffix}"
        attempts.append(attempt)

    return attempts

