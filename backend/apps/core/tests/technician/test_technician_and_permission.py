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
        print("→ setUp: Creating tenant and technician for tests...")
        self.tenant = CompanyTenant.objects.create(name="Tenant Alpha", slug="tenant-alpha")
        self.tech1 = Technician.objects.create(
            tenant=self.tenant,
            username="tech01",
            social_name="Technician One",
            technician_permission=PermissionLevel.L1
        )
        self.tech2 = Technician.objects.create(
            tenant=self.tenant,
            username="tech02",
            social_name="Technician Two",
            technician_permission=PermissionLevel.L2
        )

    def test_technician_str(self):
        print("✓ test_technician_str: __str__ should return social name and username")
        self.assertEqual(str(self.tech1), "Technician One (tech01)")

    def test_permission_flag_unique(self):
        print("✓ test_permission_flag_unique: Should prevent a duplicate for the same level+action")
        PermissionFlag.objects.create(level=PermissionLevel.L1, action="edit_order", allowed=True)
        with self.assertRaises(Exception):
            PermissionFlag.objects.create(level=PermissionLevel.L1, action="edit_order", allowed=False)

    def test_permission_flag_str(self):
        print("✓ test_permission_flag_str: __str__ should show the action with a ✔ or ✖ icon")
        flag = PermissionFlag.objects.create(level=PermissionLevel.L2, action="view_reports", allowed=False)
        self.assertIn("L2 | view_reports", str(flag))
        self.assertIn("✖", str(flag))

    def test_temporary_delegation_active_true(self):
        print("✓ test_temporary_delegation_active_true: Should return True if the current date is inside the interval")
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
        print("✓ test_temporary_delegation_active_false: Should return False if it has already expired")
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
        print("✓ test_temporary_delegation_str: __str__ should show origin, destination, and period")
        now = timezone.now()
        delegation = TemporaryDelegation.objects.create(
            tenant=self.tenant,
            from_user=self.tech1,
            to_user=self.tech2,
            valid_from=now,
            valid_until=now + timedelta(days=1)
        )
        self.assertIn("Technician One (tech01)", str(delegation))
        self.assertIn("Technician Two (tech02)", str(delegation))

    def test_delegated_action_str(self):
        print("✓ test_delegated_action_str: __str__ should show the delegation and the action")
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
        self.assertIn("Technician One", str(action))  # comes from the delegation's str
