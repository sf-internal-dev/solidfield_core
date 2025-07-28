from django.test import TestCase
from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.orders.models.service_order import ServiceOrder, ServiceOrderDownloadLink
from backend.apps.orders.services.service_order_download_service import (create_service_order_download_link_with_key, 
get_purpose_rules_for_service_order_download_link, calculate_defined_download_link_life_time)

from backend.apps.orders.services.service_order_identifier_service import create_service_order_with_identifier
class ServiceOrderDownloadLinkTests(TestCase):
    def setUp(self):
        print("→ setUp: Criando empresa, técnico e ordem de serviço para testes com geração de link de download de ordens.")
        self.company = CompanyTenant.objects.create(
            name="SolidField", slug="solidfield", tenant_code="SOLI"
        )
        self.technician = Technician.objects.create(
            username="tech1",
            tenant=self.company,
            technician_permission="L1"
        )
        self.service_order = create_service_order_with_identifier(
            company=self.company, created_by=self.technician, assigned_to=self.technician
        )

        self.service_order_download_link = create_service_order_download_link_with_key(service_order=self.service_order, 
                                                    technician=self.technician,
                                                    purpose="audit_and_compliance")

