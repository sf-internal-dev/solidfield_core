# backend/apps/core/tests/technician/test_delegation_utils.py

from django.test import TestCase
from unittest.mock import patch

from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.core.utils.technician_permission import technician_permission_temporary_delegation_util as util


class DelegationUtilsTestCase(TestCase):
    def setUp(self):
        print("→ setUp: creating tenant and L1/L2/L3 technicians")
        self.tenant = CompanyTenant.objects.create(name="TenantPerm", slug="tenant-perm")

        self.t_l1 = Technician.objects.create(
            tenant=self.tenant, username="l1", social_name="Tech L1", technician_permission="L1"
        )
        self.t_l2 = Technician.objects.create(
            tenant=self.tenant, username="l2", social_name="Tech L2", technician_permission="L2"
        )
        self.t_l3 = Technician.objects.create(
            tenant=self.tenant, username="l3", social_name="Tech L3", technician_permission="L3"
        )

        # Controlled test schema
        # - L1 has A1 (delegable) and A2 (not delegable)
        # - L2 has B1 (delegable) and selectively inherits A1 from L1
        # - L3 has C1 (delegable) and selectively inherits B1 from L2
        # - CYCLE inherits from itself, to test visited
        self.TEST_SCHEMA = {
            "L1": {
                "actions": [
                    {"code": "A1", "label": "Action 1", "delegable": True},
                    {"code": "A2", "label": "Action 2", "delegable": False},
                ]
            },
            "L2": {
                "actions": [
                    {"code": "B1", "label": "Action B1", "delegable": True},
                ],
                "inherits_selectively_from": {
                    "L1": ["A1"],  # only A1 (delegable)
                },
            },
            "L3": {
                "actions": [
                    {"code": "C1", "label": "Action C1", "delegable": True},
                ],
                "inherits_selectively_from": {
                    "L2": ["B1"],  # takes B1; A1 comes via recursion from L2→L1
                },
            },
            "CYCLE": {
                "actions": [
                    {"code": "X1", "label": "X", "delegable": True},
                ],
                "inherits_selectively_from": {
                    "CYCLE": ["X1"],  # self-reference to test visited
                },
            },
        }

    # -----------------------------
    # get_delegable_actions_deep
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_get_delegable_actions_deep_basic(self, mock_schema):
        print("✓ get_delegable_actions_deep: recursive collection, deduplicated")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # L1: only A1 (delegable)
        self.assertEqual(set(util.get_delegable_actions_deep("L1")), {"A1"})

        # L2: B1 (own) + A1 (selectively inherited from L1)
        self.assertEqual(set(util.get_delegable_actions_deep("L2")), {"B1", "A1"})

        # L3: C1 (own) + B1 (from L2) + A1 (from L1 via L2)
        self.assertEqual(set(util.get_delegable_actions_deep("L3")), {"C1", "B1", "A1"})

    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_get_delegable_actions_deep_cycle_safe(self, mock_schema):
        print("✓ get_delegable_actions_deep: tolerates a cycle (visited avoids a loop)")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # Should not hang; returns only X1 (delegable)
        self.assertEqual(set(util.get_delegable_actions_deep("CYCLE")), {"X1"})

    # -----------------------------
    # can_delegate_action
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_can_delegate_action_paths_and_delegable_flag(self, mock_schema):
        print("✓ can_delegate_action: respects paths L3→L2/L1, L2→L1 and the 'delegable' flag")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # Path rules:
        # - L3 can delegate to L2 and L1
        # - L2 can delegate to L1
        # - L1 cannot delegate to anyone

        # L3 -> L2: can delegate B1 (delegable via inheritance) and C1 (own)
        self.assertTrue(util.can_delegate_action(self.t_l3, self.t_l2, "B1"))
        self.assertTrue(util.can_delegate_action(self.t_l3, self.t_l2, "C1"))
        # But cannot delegate A2 (not delegable on L1)
        self.assertFalse(util.can_delegate_action(self.t_l3, self.t_l2, "A2"))

        # L3 -> L1: can delegate A1 (delegable on L1) and C1 (delegable on L3)
        self.assertTrue(util.can_delegate_action(self.t_l3, self.t_l1, "A1"))
        self.assertTrue(util.can_delegate_action(self.t_l3, self.t_l1, "C1"))

        # L2 -> L1: can delegate B1 (delegable on L2) and A1 (delegable, inherited from L1)
        self.assertTrue(util.can_delegate_action(self.t_l2, self.t_l1, "B1"))
        self.assertTrue(util.can_delegate_action(self.t_l2, self.t_l1, "A1"))
        # Cannot delegate A2 (not delegable) or something that does not exist
        self.assertFalse(util.can_delegate_action(self.t_l2, self.t_l1, "A2"))
        self.assertFalse(util.can_delegate_action(self.t_l2, self.t_l1, "NOPE"))

        # L1 -> L1: forbidden path
        self.assertFalse(util.can_delegate_action(self.t_l1, self.t_l1, "A1"))
        # L1 -> L2: forbidden
        self.assertFalse(util.can_delegate_action(self.t_l1, self.t_l2, "A1"))
        # L2 -> L3: forbidden (only downward)
        self.assertFalse(util.can_delegate_action(self.t_l2, self.t_l3, "B1"))
