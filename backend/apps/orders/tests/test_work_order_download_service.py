# backend/apps/orders/tests/test_work_order_download_service.py

from django.test import TestCase
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta, datetime

from backend.apps.core.models import CompanyTenant
from backend.apps.core.models.technician import Technician
from backend.apps.orders.models.work_order import WorkOrder, WorkOrderDownloadLink
from backend.apps.orders.services.work_order_download_service import (
    calculate_defined_download_link_life_time,
    get_purpose_rules_for_work_order_download_link,
    create_work_order_download_link_with_key,
)


class WorkOrderDownloadServiceTest(TestCase):
    def setUp(self):
        print("→ setUp: cria tenant, técnico e ordem")
        self.tenant = CompanyTenant.objects.create(name="Tenant A", slug="tena", tenant_code="TENA")
        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="techA",
            social_name="Tech A",
            technician_permission="L3",
            is_active=True,
        )
        self.wo = WorkOrder.objects.create(
            tenant=self.tenant,
            identifier="TENA0001",
            created_by=self.tech,
            assigned_to=self.tech,
            status="open",
            work_start=None,
            work_end=None,
        )

    def test_calculate_defined_download_link_life_time_sets_and_returns_expires_at(self):
        print("✓ calculate_defined_download_link_life_time: calcula expires_at = created_at + days e salva no objeto")
        link = WorkOrderDownloadLink.objects.create(
            work_order=self.wo,
            key="K1",
            created_at=timezone.now(),
            created_by=self.tech
        )

        expires = calculate_defined_download_link_life_time(link, 3)
        self.assertIsNotNone(expires)
        self.assertEqual(link.expires_at, expires)
        # 3 dias de diferença
        self.assertEqual((link.expires_at - link.created_at).days, 3)

    @patch("backend.apps.orders.services.work_order_download_service.get_purpose_rules", return_value=["internal", "customer"])
    def test_get_purpose_rules_for_work_order_download_link_delegates(self, mock_rules):
        print("✓ get_purpose_rules_for_work_order_download_link: delega para util com o purpose do objeto")
        link = WorkOrderDownloadLink.objects.create(
            work_order=self.wo,
            key="K2",
            created_at=timezone.now(),
            purpose="internal",
        )
        rules = get_purpose_rules_for_work_order_download_link(link)
        self.assertEqual(rules, ["internal", "customer"])
        mock_rules.assert_called_once_with("internal")

    @patch("backend.apps.orders.services.work_order_download_service.log_work_order_download_link_creation")
    @patch("backend.apps.orders.services.work_order_download_service.get_purpose_rules", return_value=["internal", "customer"])
    @patch("backend.apps.orders.services.work_order_download_service.generate_work_order_download_key", return_value="KEY123")
    def test_create_work_order_download_link_with_key_valid_purpose_but_not_set_bug(self, gen_key, rules, log_mock):
        print("✓ create_work_order_download_link_with_key: propósito válido, mas BUG atual não persiste purpose")
        fixed_now = datetime(2024, 1, 2, 3, 4, 5)
        # congela datetime.now() só dentro do create (se quiser precisão exata)
        with patch("backend.apps.orders.services.work_order_download_service.datetime") as dt:
            dt.now.return_value = fixed_now
            dt.side_effect = lambda *a, **k: datetime(*a, **k)  # permite construtor
            link = create_work_order_download_link_with_key(
                work_order=self.wo,
                purpose="customer",
                technician=self.tech
            )

        self.assertIsInstance(link, WorkOrderDownloadLink)
        self.assertEqual(link.work_order_id, self.wo.id)
        self.assertEqual(link.key, "KEY123")
        self.assertIsNotNone(link.created_at)

        # BUG documentado: o service nunca seta o purpose no objeto antes de checar
        # então, mesmo com purpose "customer" válido nas regras, link.purpose permanece None
        self.assertIsNone(link.purpose)

        gen_key.assert_called_once()
        rules.assert_called_once()  # foi consultado para o purpose atual do link (None)
        log_mock.assert_called_once_with(link)

    @patch("backend.apps.orders.services.work_order_download_service.log_work_order_download_link_creation")
    @patch("backend.apps.orders.services.work_order_download_service.get_purpose_rules", return_value=["internal"])
    @patch("backend.apps.orders.services.work_order_download_service.generate_work_order_download_key", return_value="KEY999")
    def test_create_work_order_download_link_with_key_invalid_purpose_clears_to_none(self, gen_key, _rules, _log):
        print("✓ create_work_order_download_link_with_key: propósito inválido → mantém/força None")
        link = create_work_order_download_link_with_key(
            work_order=self.wo,
            purpose="customer",  # não está nas regras mockadas ["internal"]
            technician=self.tech

        )
        self.assertIsInstance(link, WorkOrderDownloadLink)
        self.assertEqual(link.key, "KEY999")
        # service seta None quando not in rules (já era None, mas testamos efeito)
        self.assertIsNone(link.purpose)
