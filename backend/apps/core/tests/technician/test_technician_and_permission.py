from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from backend.apps.core.models import (
    Technician,
    PermissionLevel,
    PermissionFlag,
    TemporaryDelegation,
    DelegatedAction,
    CompanyTenant
)

class TechnicianPermissionModelTest(TestCase):
    def setUp(self):
        print("→ setUp: Criando tenant e técnico para testes...")
        self.tenant = CompanyTenant.objects.create(name="Tenant Alpha", slug="tenant-alpha")
        self.tech1 = Technician.objects.create(
            tenant=self.tenant,
            username="tech01",
            social_name="Técnico Um",
            technician_permission=PermissionLevel.L1
        )
        self.tech2 = Technician.objects.create(
            tenant=self.tenant,
            username="tech02",
            social_name="Técnico Dois",
            technician_permission=PermissionLevel.L2
        )

    def test_technician_str(self):
        print("✓ test_technician_str: __str__ deve retornar nome social e username")
        self.assertEqual(str(self.tech1), "Técnico Um (tech01)")

    def test_permission_flag_unique(self):
        print("✓ test_permission_flag_unique: Deve impedir criação duplicada para mesmo level+action")
        PermissionFlag.objects.create(level=PermissionLevel.L1, action="edit_order", allowed=True)
        with self.assertRaises(Exception):
            PermissionFlag.objects.create(level=PermissionLevel.L1, action="edit_order", allowed=False)

    def test_permission_flag_str(self):
        print("✓ test_permission_flag_str: __str__ deve mostrar ação com ícone ✔ ou ✖")
        flag = PermissionFlag.objects.create(level=PermissionLevel.L2, action="view_reports", allowed=False)
        self.assertIn("L2 | view_reports", str(flag))
        self.assertIn("✖", str(flag))

    def test_temporary_delegation_active_true(self):
        print("✓ test_temporary_delegation_active_true: Deve retornar True se data atual estiver no intervalo")
        now = timezone.now()
        delegation = TemporaryDelegation.objects.create(
            tenant=self.tenant,
            from_user=self.tech1,
            to_user=self.tech2,
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(hours=1)
        )
        self.assertTrue(delegation.is_active())

    def test_temporary_delegation_active_false(self):
        print("✓ test_temporary_delegation_active_false: Deve retornar False se já expirado")
        past = timezone.now() - timedelta(days=1)
        delegation = TemporaryDelegation.objects.create(
            tenant=self.tenant,
            from_user=self.tech1,
            to_user=self.tech2,
            valid_from=past - timedelta(hours=2),
            valid_until=past - timedelta(hours=1)
        )
        self.assertFalse(delegation.is_active())

    def test_temporary_delegation_str(self):
        print("✓ test_temporary_delegation_str: __str__ deve mostrar origem, destino e período")
        now = timezone.now()
        delegation = TemporaryDelegation.objects.create(
            tenant=self.tenant,
            from_user=self.tech1,
            to_user=self.tech2,
            valid_from=now,
            valid_until=now + timedelta(days=1)
        )
        self.assertIn("Técnico Um (tech01)", str(delegation))
        self.assertIn("Técnico Dois (tech02)", str(delegation))

    def test_delegated_action_str(self):
        print("✓ test_delegated_action_str: __str__ deve mostrar delegação e ação")
        now = timezone.now()
        delegation = TemporaryDelegation.objects.create(
            tenant=self.tenant,
            from_user=self.tech1,
            to_user=self.tech2,
            valid_from=now,
            valid_until=now + timedelta(days=1)
        )
        action = DelegatedAction.objects.create(delegation=delegation, action="edit_order")
        self.assertIn("edit_order", str(action))
        self.assertIn("Técnico Um", str(action))  # proveniente do str do delegation
