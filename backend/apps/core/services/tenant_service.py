from core.models.tenant import CompanyTenant
from backend.apps.core.utils.tenant_identifier_code_util import generate_tenant_identifier_code

def create_company_with_slug(nome: str, slug: str) -> CompanyTenant:
    code = generate_tenant_identifier_code(slug)
    """ Essa provavelmente não vai ser o unico field processado por uma util antes de entrar no banco de dados,
        Então devo reconsiderar talvez só gerar o code por
    """
    company = CompanyTenant.objects.create(name=nome, slug=slug, tenant_code=code)
    return company