import re
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from backend.apps.core.models.tenant import CompanyTenant

def generate_tenant_identifier_code(slug: str, max_tries: int = 30) -> str:
    """Generates an unique tenant code based on the tenant slug. 
    Example: slug=solidfield, tenant_code=SOLI, SOLI1, SOLI2"""
    base = re.sub(r'[^A-Z0-9]', '', slug.upper())[:4] or "EMPR"
    base = base[:4] 
    for i in range(max_tries):
        sufixo = "" if i == 0 else str(i)
        tentativa = f"{base}{sufixo}"
        if not CompanyTenant.objects.filter(tenant_code=tentativa).exists():
            return tentativa

    # forced Fallback: SOLIAB (ex: base + random letters)
    return f"{base}{get_random_string(length=2).upper()}"


