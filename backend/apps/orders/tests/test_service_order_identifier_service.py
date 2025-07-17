from django.test import TestCase
from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.orders.models.service_order import ServiceOrder
from backend.apps.orders.services.service_order_identifier_service import create_service_order_with_identifier


class ServiceOrderIdentifierTests(TestCase):
    def setUp(self):
        print("→ setUp: Criando empresa e técnico para testes de identificação de ordens.")
        self.company = CompanyTenant.objects.create(
            name="SolidField", slug="solidfield", tenant_code="SOLI"
        )
        self.technician = Technician.objects.create(
            username="tech1",
            tenant=self.company,
            technician_permission="L1"
        )

    def test_first_service_order_identifier(self):
        print("✓ test_first_service_order_identifier: Deve gerar SOLI0001 como primeira ordem.")
        order = create_service_order_with_identifier(
            company=self.company,
            created_by=self.technician,
            assigned_to=self.technician,
        )
        self.assertEqual(order.identifier, "SOLI0001")

    def test_sequential_identifiers(self):
        print("✓ test_sequential_identifiers: Deve gerar identificadores sequenciais.")
        for _ in range(3):
            create_service_order_with_identifier(
                company=self.company,
                created_by=self.technician,
                assigned_to=self.technician,
            )

        last_order = create_service_order_with_identifier(
            company=self.company,
            created_by=self.technician,
            assigned_to=self.technician,
        )
        self.assertEqual(last_order.identifier, "SOLI0004")

    def test_identifier_rollover_after_9999(self):
        print("✓ test_identifier_rollover_after_9999: Deve gerar número com 5 dígitos após 9999.")
        ServiceOrder.objects.create(
            tenant=self.company,
            identifier="SOLI9999",
            created_by=self.technician,
            assigned_to=self.technician,
            
        )
        order = create_service_order_with_identifier(
            company=self.company,
            created_by=self.technician,
            assigned_to=self.technician,

        )
        self.assertEqual(order.identifier, "SOLI10000")
