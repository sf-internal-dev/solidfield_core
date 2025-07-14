from backend.apps.core.utils.tenant.tenant_slug_util import sanitize_tenant_slug, suggest_company_slug
from backend.apps.core.utils.tenant.tenant_identifier_code_util import generate_tenant_identifier_code
from core.models.tenant import CompanyTenant


# -> Resolves a unique slug based on the company name
# Tries cleaned username-style suggestions and checks availability
# If all are taken, falls back to a numeric suffix strategy
def resolve_available_slug_from_name(company_name: str) -> str:
    suggestions = suggest_company_slug(company_name)

    for suggestion in suggestions:
        if not CompanyTenant.objects.filter(slug=suggestion).exists():
            return suggestion

    base_slug = sanitize_tenant_slug(company_name)
    if not base_slug:
        base_slug = "tenant"

    for i in range(1, 30):
        slug_attempt = f"{base_slug}{i}"
        if not CompanyTenant.objects.filter(slug=slug_attempt).exists():
            return slug_attempt

    raise ValueError("Couldn't create a slug suggestion for your company. Please choose one manually.")


# -> Generates a unique tenant_code based on the slug
# Iterates over identifier suggestions and checks availability
# If exhausted, falls back to a random suffix strategy
def generate_valid_tenant_code(slug: str) -> str:
    for attempt in generate_tenant_identifier_code(slug):
        if not CompanyTenant.objects.filter(tenant_code=attempt).exists():
            return attempt

    base = generate_tenant_identifier_code(slug)[0][:4]
    return f"{base}{generate_tenant_identifier_code(length=2).upper()}"


# -> Prepares both slug and tenant_code for a new CompanyTenant
# Ensures both values are unique and derived from the company name
def prepare_company_slug_and_code(company_name: str) -> dict:
    slug = resolve_available_slug_from_name(company_name)
    code = generate_valid_tenant_code(slug)

    return {
        "slug": slug,
        "tenant_code": code
    }
