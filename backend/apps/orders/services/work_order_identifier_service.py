# backend.apps.orders.services.service_order_identifier_service.py

import re
from django.db.models import Max
from backend.apps.orders.utils.service_order_identifier_util import generate_service_order_identifier
from backend.apps.orders.models.service_order import ServiceOrder
from backend.apps.core.models.tenant import CompanyTenant
from backend.apps.core.services.audition_log_service import log_service_order_creation

# -> Creates a service order linked to a company with a unique tenant-based identifier
# Format: <TENANT_CODE><4-digit number>, e.g., SOLI0001, UGAF0010
# The number is sequential and scoped per tenant_code (not global)
# Uses the last created ServiceOrder's identifier for the same tenant and increments from it
def create_service_order_with_identifier(company: CompanyTenant, **order_data):
    tenant_code = company.tenant_code
    last_identifier = (
        ServiceOrder.objects
        .filter(tenant__tenant_code=tenant_code)
        .aggregate(max_id=Max("identifier"))
        .get("max_id")
    )

    if last_identifier:
        match = re.match(rf"^{re.escape(tenant_code)}(\d+)$", last_identifier)
        try:
            last_number = int(match.group(1)) if match else 0
        except ValueError:
            last_number = 0
    else:
        last_number = 0

    new_identifier = generate_service_order_identifier(tenant_code, last_number)
    service_order = ServiceOrder.objects.create(
        tenant=company,
        identifier=new_identifier,
        **order_data
    )

    log_service_order_creation(service_order)

    return service_order
