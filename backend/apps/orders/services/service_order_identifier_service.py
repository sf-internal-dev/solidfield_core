# backend.apps.orders.services.service_order_identifier_service.py

from backend.apps.orders.utils.service_order_identifier_util import generate_service_order_identifier
from backend.apps.orders.models.service_order import ServiceOrder
from backend.apps.core.models.tenant import CompanyTenant
from django.db.models import Max


# -> creates a service order base related to a company and with it's tenant_code for identifier
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
        tenant=company,
        identifier=new_identifier,
        **order_data
    )
