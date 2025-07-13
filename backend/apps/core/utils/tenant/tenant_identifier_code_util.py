import re
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from backend.apps.core.models.tenant import CompanyTenant
import unicodedata

def generate_tenant_identifier_code(slug: str, max_tries: int = 30) -> str:
    """Generates an unique tenant code based on the tenant slug."""
    normalized = unicodedata.normalize("NFKD", slug)
    ascii_slug = normalized.encode("ascii", "ignore").decode("ascii")
    base = re.sub(r'[^A-Z0-9]', '', ascii_slug.upper())[:4] or "COMP"
    base = base[:4]

    for i in range(max_tries):
        suffix = "" if i == 0 else str(i)
        attempt = f"{base}{suffix}"
        if not CompanyTenant.objects.filter(tenant_code=attempt).exists():
            return attempt

    return f"{base}{get_random_string(length=2).upper()}"
