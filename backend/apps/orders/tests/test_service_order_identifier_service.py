from django.test import TestCase
from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.orders.models.work_order import WorkOrder
from backend.apps.orders.services.work_order_identifier_service import create_work_order_with_identifier


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
        order = create_work_order_with_identifier(
            company=self.company, created_by=self.technician, assigned_to=self.technician
        )
        self.assertEqual(order.identifier, "SOLI0001")

    def test_sequential_identifiers(self):
        print("✓ test_sequential_identifiers: Deve gerar identificadores sequenciais.")
        for _ in range(3):
            create_work_order_with_identifier(
                company=self.company, created_by=self.technician, assigned_to=self.technician
            )
        order = create_work_order_with_identifier(
            company=self.company, created_by=self.technician, assigned_to=self.technician
        )
        self.assertEqual(order.identifier, "SOLI0004")

    def test_identifier_rollover_after_9999(self):
        print("✓ test_identifier_rollover_after_9999: Deve gerar número com 5 dígitos após 9999.")
        WorkOrder.objects.create(
            tenant=self.company,
            identifier="SOLI9999",
            created_by=self.technician,
            assigned_to=self.technician,
        )
        order = create_work_order_with_identifier(
            company=self.company, created_by=self.technician, assigned_to=self.technician
        )
        self.assertEqual(order.identifier, "SOLI10000")

    def test_identifier_ignores_invalid_existing(self):
        print("✓ test_identifier_ignores_invalid_existing: Ignora identificador inválido e começa do 1.")
        WorkOrder.objects.create(
            tenant=self.company,
            identifier="SOLIabcd",
            created_by=self.technician,
            assigned_to=self.technician,
        )
        order = create_work_order_with_identifier(
            company=self.company, created_by=self.technician, assigned_to=self.technician
        )
        self.assertEqual(order.identifier, "SOLI0001")

    def test_multiple_companies_have_independent_sequences(self):
        print("✓ test_multiple_companies_have_independent_sequences: Cada empresa deve ter sua própria contagem.")
        another_company = CompanyTenant.objects.create(
            name="BetaCorp", slug="betacorp", tenant_code="BETA"
        )
        tech2 = Technician.objects.create(
            username="tech2",
            tenant=another_company,
            technician_permission="L1"
        )

        create_work_order_with_identifier(
            company=self.company, created_by=self.technician, assigned_to=self.technician
        )
        create_work_order_with_identifier(
            company=self.company, created_by=self.technician, assigned_to=self.technician
        )

        order_beta = create_work_order_with_identifier(
            company=another_company, created_by=tech2, assigned_to=tech2
        )

        self.assertEqual(order_beta.identifier, "BETA0001")
