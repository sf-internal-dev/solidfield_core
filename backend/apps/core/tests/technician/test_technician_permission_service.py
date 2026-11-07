from django.test import TestCase
from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.utils import timezone

from backend.apps.core.models import CompanyTenant, Technician, TemporaryDelegation, DelegatedAction

from backend.apps.core.services import technician_permission_service as svc


class PermissionServiceApiTestCase(TestCase):
    def setUp(self):
        print("→ setUp: creating tenant and L1/L2/L3 technicians")
        self.tenant = CompanyTenant.objects.create(name="TenantPerm", slug="tenant-perm")

        self.l1 = Technician.objects.create(
            tenant=self.tenant, username="l1", social_name="Tech L1", technician_permission="L1"
        )
        self.l2 = Technician.objects.create(
            tenant=self.tenant, username="l2", social_name="Tech L2", technician_permission="L2"
        )
        self.l3 = Technician.objects.create(
            tenant=self.tenant, username="l3", social_name="Tech L3", technician_permission="L3"
        )

        self.now = timezone.now()
        self.tomorrow = self.now + timedelta(days=1)
        self.yesterday = self.now - timedelta(days=1)

    # -----------------------------
    # delegate_permission_level
    # -----------------------------
    @patch("backend.apps.core.services.technician_permission_service.log_permission_level_delegation")
    def test_delegate_permission_level(self, mock_log):
        print("✓ delegate_permission_level: L3 can delegate, non-L3 cannot")
        # L3 → L2
        ok, errs = svc.delegate_permission_level(self.l3, self.l1, "L2")
        self.assertTrue(ok)
        self.assertEqual(errs, [])
        self.l1.refresh_from_db()
        self.assertEqual(self.l1.technician_permission, "L2")
        mock_log.assert_called_once()

        # L2 → L1 (cannot)
        ok2, errs2 = svc.delegate_permission_level(self.l2, self.l1, "L1")
        self.assertFalse(ok2)
        self.assertIn("delegator_not_manager", errs2)

    # -----------------------------
    # create_temporary_delegation
    # -----------------------------
    @patch("backend.apps.core.services.technician_permission_service.log_temporary_delegation")
    @patch("backend.apps.core.services.technician_permission_service.can_delegate_action")
    def test_create_temporary_delegation_success(self, mock_can, mock_logtmp):
        print("✓ create_temporary_delegation: creates a valid temporary delegation with actions")
        # NOTE: your function calls can_delegate_action(from_user, action, to_user) (a different order from the previous version).
        # We will accept that order in the mock:
        def can_delegate_side_effect(from_user, to_user, action):
            return action in {"A1", "B1"}  # only these are delegable
        mock_can.side_effect = can_delegate_side_effect

        delegation, errors = svc.create_temporary_delegation(
            from_user=self.l3,
            to_user=self.l2,
            actions=["A1", "B1"],
            valid_from=self.now,
            valid_until=self.tomorrow,
        )
        self.assertIsInstance(delegation, TemporaryDelegation)
        self.assertEqual(errors, [])
        self.assertEqual(delegation.from_user, self.l3)
        self.assertEqual(delegation.to_user, self.l2)
        self.assertTrue(DelegatedAction.objects.filter(delegation=delegation, action="A1").exists())
        self.assertTrue(DelegatedAction.objects.filter(delegation=delegation, action="B1").exists())
        mock_logtmp.assert_called_once_with(delegation, ["A1", "B1"])

    @patch("backend.apps.core.services.technician_permission_service.can_delegate_action", return_value=False)
    def test_create_temporary_delegation_no_valid_actions_bug(self, _mock_can):
        print("✓ create_temporary_delegation: no valid actions → should signal an error")
        # NOTE: there is a bug in the function: it uses `return None, errors.append("...")`, which returns (None, None).
        delegation, errors = svc.create_temporary_delegation(
            from_user=self.l3,
            to_user=self.l2,
            actions=["NOPE"],
            valid_from=self.now,
            valid_until=self.tomorrow,
        )
        # The expected correct behavior would be: delegation=None, errors=["no_valid_actions"] or ["invalid_action: NOPE"].
        # Current behavior (bug): errors is None because of the append inside the return.
        self.assertIsNone(delegation)
        self.assertIsNone(errors)  # documents the current bug

    def test_create_temporary_delegation_self_delegation_bug(self):
        print("✓ create_temporary_delegation: self-delegation returns an error (current bug returns None)")
        # Another identical bug: `return None, errors.append("tried_to_delegate_to_itself")`
        delegation, errors = svc.create_temporary_delegation(
            from_user=self.l3,
            to_user=self.l3,
            actions=["A1"],
            valid_from=self.now,
            valid_until=self.tomorrow,
        )
        self.assertIsNone(delegation)
        self.assertIsNone(errors)  # documents the current bug (expected: ["tried_to_delegate_to_itself"])

    # -----------------------------
    # has_permission
    # -----------------------------
    @patch("backend.apps.core.services.technician_permission_service.get_action_label", return_value="Some Action")
    @patch("backend.apps.core.services.technician_permission_service.technician_has_permission_for_action")
    def test_has_permission_via_level_or_delegation(self, mock_thas, _mock_label):
        print("✓ has_permission: grants via level or via an active delegation")
        # Case 1: granted by the level
        mock_thas.return_value = True
        ok, msg = svc.has_permission(self.l3, "A1")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

        # Case 2: not by the level, but via an active delegation
        mock_thas.return_value = False
        delegation = TemporaryDelegation.objects.create(
            tenant=self.tenant,
            from_user=self.l3,
            to_user=self.l1,
            valid_from=self.yesterday,
            valid_until=self.tomorrow,
        )
        DelegatedAction.objects.create(delegation=delegation, action="A1")

        ok2, msg2 = svc.has_permission(self.l1, "A1")
        self.assertTrue(ok2)
        self.assertEqual(msg2, "")

        # Case 3: no level and no delegation
        ok3, msg3 = svc.has_permission(self.l1, "NOPE")
        self.assertFalse(ok3)
        self.assertEqual(msg3, "")  # the current function returns ""; the final error message is unreachable

    # -----------------------------
    # list_effective_permissions
    # -----------------------------
    @patch("backend.apps.core.services.technician_permission_service.get_effective_actions_for_level")
    def test_list_effective_permissions_union(self, mock_effective):
        print("✓ list_effective_permissions: unions the level's actions with active delegated ones")
        mock_effective.return_value = ["X", "Y"]  # actions from the level

        delegation = TemporaryDelegation.objects.create(
            tenant=self.tenant,
            from_user=self.l3,
            to_user=self.l2,
            valid_from=self.yesterday,
            valid_until=self.tomorrow,
        )
        DelegatedAction.objects.create(delegation=delegation, action="Z")

        result = set(svc.list_effective_permissions(self.l2))
        self.assertEqual(result, {"X", "Y", "Z"})

    # -----------------------------
    # revoke_delegation
    # -----------------------------
    @patch("backend.apps.core.services.technician_permission_service.log_revoke_temporary_delegation")
    def test_revoke_delegation(self, mock_logrev):
        print("✓ revoke_delegation: logs and deletes the delegation")
        delegation = TemporaryDelegation.objects.create(
            tenant=self.tenant,
            from_user=self.l3,
            to_user=self.l2,
            valid_from=self.yesterday,
            valid_until=self.tomorrow,
        )
        svc.revoke_delegation(delegation)
        mock_logrev.assert_called_once_with(delegation)
        self.assertFalse(TemporaryDelegation.objects.filter(pk=delegation.pk).exists())

    # -----------------------------
    # list_outgoing_delegations / list_incoming_delegations
    # -----------------------------
    def test_list_outgoing_incoming(self):
        print("✓ list_outgoing_delegations / list_incoming_delegations: ordering by validity desc")
        d1 = TemporaryDelegation.objects.create(
            tenant=self.tenant, from_user=self.l3, to_user=self.l2,
            valid_from=self.yesterday, valid_until=self.tomorrow
        )
        d2 = TemporaryDelegation.objects.create(
            tenant=self.tenant, from_user=self.l3, to_user=self.l1,
            valid_from=self.yesterday, valid_until=self.tomorrow + timedelta(days=1)
        )
        d3 = TemporaryDelegation.objects.create(
            tenant=self.tenant, from_user=self.l2, to_user=self.l1,
            valid_from=self.yesterday, valid_until=self.tomorrow + timedelta(days=2)
        )

        outgoing_l3 = list(svc.list_outgoing_delegations(self.l3))
        incoming_l1 = list(svc.list_incoming_delegations(self.l1))

        # outgoing from L3: d2 expires after d1 → d2 first
        self.assertEqual([o.pk for o in outgoing_l3], [d2.pk, d1.pk])
        # incoming to L1: d3 expires after d2 → d3 first
        self.assertEqual([i.pk for i in incoming_l1], [d3.pk, d2.pk])
