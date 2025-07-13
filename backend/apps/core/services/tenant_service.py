from core.models.tenant import CompanyTenant
from backend.apps.core.utils.tenant.tenant_identifier_code_util import generate_tenant_identifier_code

def create_company_with_slug(nome: str, slug: str) -> CompanyTenant:
    code = generate_tenant_identifier_code(slug)
    company = CompanyTenant.objects.create(name=nome, slug=slug, tenant_code=code)
    return company