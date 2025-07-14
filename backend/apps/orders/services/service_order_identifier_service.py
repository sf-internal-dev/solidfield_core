from backend.apps.orders.utils.service_order_identifier_util import generate_service_order_identifier
from backend.apps.orders.models.service_order import ServiceOrder
from backend.apps.core.models.tenant import CompanyTenant
from django.db.models import Max

def create_service_order_with_identifier(company: CompanyTenant, **order_data):
    tenant_code = company.tenant_code
    last_identifier = (
        ServiceOrder.objects
        .filter(tenant_code=tenant_code)
        .aggregate(max_id=Max("identifier"))
        .get("max_id")
    )

    if last_identifier:
        try:
            last_number = int(last_identifier.replace(tenant_code, ""))
        except ValueError:
            last_number = 0
    else:
        last_number = 0

    new_identifier = generate_service_order_identifier(tenant_code, last_number)

    return ServiceOrder.objects.create(
        tenant_code=tenant_code,
        identifier=new_identifier,
        **order_data
    )
