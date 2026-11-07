# backend/apps/core/tests/test_permission_utils.py

from django.test import TestCase
from unittest.mock import patch

from backend.apps.core.models import CompanyTenant, Technician
# ⬇️ adjust this import to the REAL path of your functions module:
from backend.apps.core.utils.technician_permission import technician_permission_delegation_util as util


class PermissionUtilsPatchedSchemaTest(TestCase):
    def setUp(self):
        print("→ setUp: creating tenant and L1/L3 technicians")
        self.tenant = CompanyTenant.objects.create(name="TenantPerm", slug="tenant-perm")

        self.t_l1 = Technician.objects.create(
            tenant=self.tenant, username="l1", social_name="Tech L1", technician_permission="L1"
        )
        self.t_l3 = Technician.objects.create(
            tenant=self.tenant, username="l3", social_name="Tech L3", technician_permission="L3"
        )

        # Controlled test schema (does not depend on the real production schema)
        self.TEST_SCHEMA = {
            "L1": {
                "label": "Execution (Field Level)",
                "actions": [
                    {"code": "A1", "label": "Action 1"},
                    {"code": "A2", "label": "Action 2"},
                ],
                # no inheritance
            },
            "L2": {
                "label": "Coordination (Local Supervision)",
                "actions": [
                    {"code": "B1", "label": "Action B1"},
                ],
                # inherits SELECTIVELY ONLY A1 from L1
                "inherits_selectively_from": {
                    "L1": ["A1"],
                },
            },
            "L3": {
                "label": "Full Control (Operational Management)",
                "actions": [
                    {"code": "C1", "label": "Action C1"},
                ],
                # inherits SELECTIVELY B1 from L2 (and via recursion will also bring A1)
                "inherits_selectively_from": {
                    "L2": ["B1"],
                },
            },
            # cyclic level to test 'visited' protection
            "CYCLE": {
                "label": "Cycle",
                "actions": [],
                "inherits_selectively_from": {
                    "CYCLE": ["A1"],  # self-reference
                },
            },
        }

    # -----------------------------
    # is_manager
    # -----------------------------
    def test_is_manager(self):
        print("✓ is_manager: L3 True, L1 False")
        self.assertTrue(util.is_manager(self.t_l3))
        self.assertFalse(util.is_manager(self.t_l1))

    # -----------------------------
    # delegate_complete_permission_level
    # -----------------------------
    def test_delegate_complete_permission_level(self):
        print("✓ delegate_complete_permission_level: L3 can delegate, L1 cannot")
        # L3 delegates: should change L1's level to L2
        ok = util.delegate_complete_permission_level(self.t_l3, self.t_l1, "L2")
        self.assertTrue(ok)
        self.t_l1.refresh_from_db()
        self.assertEqual(self.t_l1.technician_permission, "L2")

        # L1 tries to delegate: should fail and not change anything
        ok2 = util.delegate_complete_permission_level(self.t_l1, self.t_l3, "L1")
        self.assertFalse(ok2)
        self.t_l3.refresh_from_db()
        self.assertEqual(self.t_l3.technician_permission, "L3")

    # -----------------------------
    # get_effective_actions_for_level
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_get_effective_actions_for_level_selective_and_recursive(self, mock_schema):
        print("✓ get_effective_actions_for_level: selective inheritance + recursion without a loop")
        # injects a fake schema
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # L1: only its own actions
        a_l1 = set(util.get_effective_actions_for_level("L1"))
        self.assertEqual(a_l1, {"A1", "A2"})

        # L2: its own actions + selective ones from L1 (A1)
        a_l2 = set(util.get_effective_actions_for_level("L2"))
        self.assertEqual(a_l2, {"B1", "A1", "A2"})

        # L3: its own actions + B1 from L2 + (via recursion) A1 from L1
        a_l3 = set(util.get_effective_actions_for_level("L3"))
        self.assertEqual(a_l3, {"C1", "B1", "A1", "A2"})

        # level with a cycle: should not hang or duplicate forever
        a_cycle = set(util.get_effective_actions_for_level("CYCLE"))
        self.assertIn("A1", a_cycle)  # came from its own selective mapping
        # nothing beyond that, since there are no own actions or other branches

    # -----------------------------
    # get_effective_action_objects_for_level
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_get_effective_action_objects_for_level_strict_selective(self, mock_schema):
        print("✓ get_effective_action_objects_for_level: respects selection by code of the current level")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # For L2: objects for B1 (own) + A1 (selectively inherited from L1)
        objs_l2 = util.get_effective_action_objects_for_level("L2")
        codes_l2 = {o["code"] for o in objs_l2}
        self.assertEqual(codes_l2, {"B1", "A1"})
        labels_l2 = {o["label"] for o in objs_l2}
        self.assertIn("Action B1", labels_l2)
        self.assertIn("Action 1", labels_l2)
        self.assertNotIn("Action 2", labels_l2)  # A2 was not listed in the inheritance

        # For L3: objects for C1 (own) + B1 (inherited from L2)
        # (A1 is not included here because L3 did not list it in the inheritance of the immediately inherited level)
        objs_l3 = util.get_effective_action_objects_for_level("L3")
        codes_l3 = {o["code"] for o in objs_l3}
        self.assertEqual(codes_l3, {"C1", "B1"})

    # -----------------------------
    # get_action_label
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_get_action_label(self, mock_schema):
        print("✓ get_action_label: finds the correct label via effective objects")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        self.assertEqual(util.get_action_label("L2", "A1"), "Action 1")
        self.assertIsNone(util.get_action_label("L2", "A2"))  # not inherited by L2

    # -----------------------------
    # technician_has_permission_for_action
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_technician_has_permission_for_action(self, mock_schema):
        print("✓ technician_has_permission_for_action: uses the effective set for the technician's level")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # after delegation, L1 -> L2
        ok = util.delegate_complete_permission_level(self.t_l3, self.t_l1, "L2")
        self.assertTrue(ok)
        self.t_l1.refresh_from_db()
        self.assertEqual(self.t_l1.technician_permission, "L2")

        # L2 should have B1 and A1, but not A2
        self.assertTrue(util.technician_has_permission_for_action(self.t_l1, "B1"))
        self.assertTrue(util.technician_has_permission_for_action(self.t_l1, "A1"))
        self.assertTrue(util.technician_has_permission_for_action(self.t_l1, "A2"))
