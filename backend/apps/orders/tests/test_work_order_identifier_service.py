# backend/apps/orders/tests/test_work_order_identifier_service.py

from django.test import TestCase
from unittest.mock import patch
from django.utils import timezone

from backend.apps.core.models import CompanyTenant
from backend.apps.core.models.technician import Technician
from backend.apps.orders.models.work_order import WorkOrder
from backend.apps.orders.services.work_order_identifier_service import create_work_order_with_identifier


class CreateWorkOrderWithIdentifierTest(TestCase):
    def setUp(self):
        print("→ setUp: criando tenants e técnicos básicos")
        self.tenant1 = CompanyTenant.objects.create(name="Tenant A", slug="tena", tenant_code="TENA")
        self.tenant2 = CompanyTenant.objects.create(name="Tenant B", slug="tenb", tenant_code="TENB")

        self.tech_a = Technician.objects.create(
            tenant=self.tenant1, username="techA", social_name="Tech A", technician_permission="L3", is_active=True
        )
        self.tech_b = Technician.objects.create(
            tenant=self.tenant2, username="techB", social_name="Tech B", technician_permission="L3", is_active=True
        )

        self.now = timezone.now()

    @patch("backend.apps.orders.services.work_order_identifier_service.log_work_order_creation")
    @patch("backend.apps.orders.services.work_order_identifier_service.generate_work_order_identifier", return_value="TENA0001")
    def test_first_identifier_starts_at_0001(self, gen_mock, log_mock):
        print("✓ create_work_order_with_identifier: sem ordens prévias → usa last_number=0 e gera 0001")
        wo = create_work_order_with_identifier(
            self.tenant1,
            created_by=self.tech_a,
            assigned_to=self.tech_a,
            status="open",
            work_start=self.now,
            work_end=self.now,
        )

        self.assertIsInstance(wo, WorkOrder)
        self.assertEqual(wo.tenant_id, self.tenant1.id)
        self.assertEqual(wo.identifier, "TENA0001")

        args, kwargs = gen_mock.call_args
        self.assertEqual(args[0], "TENA")
        self.assertEqual(args[1], 0)

        log_mock.assert_called_once_with(wo)

    @patch("backend.apps.orders.services.work_order_identifier_service.log_work_order_creation")
    @patch("backend.apps.orders.services.work_order_identifier_service.generate_work_order_identifier", return_value="TENA0013")
    def test_increments_from_last_identifier_same_tenant(self, gen_mock, _log_mock):
        print("✓ create_work_order_with_identifier: incrementa a partir do último ID do MESMO tenant")
        WorkOrder.objects.create(
            tenant=self.tenant1,
            identifier="TENA0012",
            created_by=self.tech_a,
            assigned_to=self.tech_a,
            status="open",
            work_start=self.now,
            work_end=self.now,
        )
        WorkOrder.objects.create(
            tenant=self.tenant2,
            identifier="TENB0099",
            created_by=self.tech_b,
            assigned_to=self.tech_b,
            status="open",
            work_start=self.now,
            work_end=self.now,
        )

        wo = create_work_order_with_identifier(
            self.tenant1,
            created_by=self.tech_a,
            assigned_to=self.tech_a,
            status="open",
            work_start=self.now,
            work_end=self.now,
        )

        self.assertEqual(wo.identifier, "TENA0013")
        args, _ = gen_mock.call_args
        self.assertEqual(args[0], "TENA")
        self.assertEqual(args[1], 12)

    @patch("backend.apps.orders.services.work_order_identifier_service.log_work_order_creation")
    @patch("backend.apps.orders.services.work_order_identifier_service.generate_work_order_identifier", return_value="TENA0001")
    def test_malformed_last_identifier_fallsback_to_zero(self, gen_mock, _log_mock):
        print("✓ create_work_order_with_identifier: último ID malformado → considera last_number=0")
        WorkOrder.objects.create(
            tenant=self.tenant1,
            identifier="TENA-ABC",
            created_by=self.tech_a,
            assigned_to=self.tech_a,
            status="open",
            work_start=self.now,
            work_end=self.now,
        )

        wo = create_work_order_with_identifier(
            self.tenant1,
            created_by=self.tech_a,
            assigned_to=self.tech_a,
            status="open",
            work_start=self.now,
            work_end=self.now,
        )
        self.assertEqual(wo.identifier, "TENA0001")
        args, _ = gen_mock.call_args
        self.assertEqual(args[0], "TENA")
        self.assertEqual(args[1], 0)

    @patch("backend.apps.orders.services.work_order_identifier_service.log_work_order_creation")
    @patch("backend.apps.orders.services.work_order_identifier_service.generate_work_order_identifier")
    def test_scoped_per_tenant_does_not_mix_sequences(self, gen_mock, _log_mock):
        print("✓ create_work_order_with_identifier: sequência isolada por tenant_code")
        WorkOrder.objects.create(
            tenant=self.tenant1,
            identifier="TENA0009",
            created_by=self.tech_a,
            assigned_to=self.tech_a,
            status="open",
            work_start=self.now,
            work_end=self.now,
        )
        WorkOrder.objects.create(
            tenant=self.tenant2,
            identifier="TENB0003",
            created_by=self.tech_b,
            assigned_to=self.tech_b,
            status="open",
            work_start=self.now,
            work_end=self.now,
        )

        def gen_side_effect(code, last):
            if code == "TENA" and last == 9:
                return "TENA0010"
            if code == "TENB" and last == 3:
                return "TENB0004"
            return f"{code}{last+1:04d}"

        gen_mock.side_effect = gen_side_effect

        wo1 = create_work_order_with_identifier(
            self.tenant1,
            created_by=self.tech_a,
            assigned_to=self.tech_a,
            status="open",
            work_start=self.now,
            work_end=self.now,
        )
        wo2 = create_work_order_with_identifier(
            self.tenant2,
            created_by=self.tech_b,
            assigned_to=self.tech_b,
            status="open",
            work_start=self.now,
            work_end=self.now,
        )

        self.assertEqual(wo1.identifier, "TENA0010")
        self.assertEqual(wo2.identifier, "TENB0004")

    @patch("backend.apps.orders.services.work_order_identifier_service.generate_work_order_identifier", return_value="TENB0001")
    @patch("backend.apps.orders.services.work_order_identifier_service.log_work_order_creation")
    def test_returns_work_order_instance_and_logs(self, _log_mock, _gen_mock):
        print("✓ create_work_order_with_identifier: retorna WorkOrder e executa log")
        wo = create_work_order_with_identifier(
            self.tenant2,
            created_by=self.tech_b,
            assigned_to=self.tech_b,
            status="queued",
            work_start=None,
            work_end=None,
        )
        self.assertIsInstance(wo, WorkOrder)
        self.assertEqual(wo.identifier, "TENB0001")
        self.assertEqual(wo.status, "queued")
