# backend/apps/core/tests/technician/test_delegation_utils.py

from django.test import TestCase
from unittest.mock import patch

from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.core.utils.technician_permission import technician_permission_temporary_delegation_util as util


class DelegationUtilsTestCase(TestCase):
    def setUp(self):
        print("→ setUp: criando tenant e técnicos L1/L2/L3")
        self.tenant = CompanyTenant.objects.create(name="TenantPerm", slug="tenant-perm")

        self.t_l1 = Technician.objects.create(
            tenant=self.tenant, username="l1", social_name="Tec L1", technician_permission="L1"
        )
        self.t_l2 = Technician.objects.create(
            tenant=self.tenant, username="l2", social_name="Tec L2", technician_permission="L2"
        )
        self.t_l3 = Technician.objects.create(
            tenant=self.tenant, username="l3", social_name="Tec L3", technician_permission="L3"
        )

        # Schema de teste controlado
        # - L1 tem A1 (delegable) e A2 (não delegable)
        # - L2 tem B1 (delegable) e herda seletivamente A1 de L1
        # - L3 tem C1 (delegable) e herda seletivamente B1 de L2
        # - CYCLE herda de si mesmo, para testar visited
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
                    "L1": ["A1"],  # só A1 (delegable)
                },
            },
            "L3": {
                "actions": [
                    {"code": "C1", "label": "Action C1", "delegable": True},
                ],
                "inherits_selectively_from": {
                    "L2": ["B1"],  # pega B1; A1 vem via recursão de L2→L1
                },
            },
            "CYCLE": {
                "actions": [
                    {"code": "X1", "label": "X", "delegable": True},
                ],
                "inherits_selectively_from": {
                    "CYCLE": ["X1"],  # auto-referência para testar visited
                },
            },
        }

    # -----------------------------
    # get_delegable_actions_deep
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_get_delegable_actions_deep_basic(self, mock_schema):
        print("✓ get_delegable_actions_deep: coleta recursiva e deduplicada")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # L1: apenas A1 (delegable)
        self.assertEqual(set(util.get_delegable_actions_deep("L1")), {"A1"})

        # L2: B1 (própria) + A1 (herdada seletiva de L1)
        self.assertEqual(set(util.get_delegable_actions_deep("L2")), {"B1", "A1"})

        # L3: C1 (própria) + B1 (de L2) + A1 (de L1 via L2)
        self.assertEqual(set(util.get_delegable_actions_deep("L3")), {"C1", "B1", "A1"})

    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_get_delegable_actions_deep_cycle_safe(self, mock_schema):
        print("✓ get_delegable_actions_deep: tolera ciclo (visited evita loop)")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # Não deve travar; retorna apenas X1 (delegable)
        self.assertEqual(set(util.get_delegable_actions_deep("CYCLE")), {"X1"})

    # -----------------------------
    # can_delegate_action
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_can_delegate_action_paths_and_delegable_flag(self, mock_schema):
        print("✓ can_delegate_action: respeita caminhos L3→L2/L1, L2→L1 e flag 'delegable'")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # Regras de caminho:
        # - L3 pode delegar para L2 e L1
        # - L2 pode delegar para L1
        # - L1 não pode delegar para ninguém

        # L3 -> L2: pode delegar B1 (delegable via herança) e C1 (própria)
        self.assertTrue(util.can_delegate_action(self.t_l3, self.t_l2, "B1"))
        self.assertTrue(util.can_delegate_action(self.t_l3, self.t_l2, "C1"))
        # Mas não pode delegar A2 (não delegable em L1)
        self.assertFalse(util.can_delegate_action(self.t_l3, self.t_l2, "A2"))

        # L3 -> L1: pode delegar A1 (delegable em L1) e C1 (delegable no L3)
        self.assertTrue(util.can_delegate_action(self.t_l3, self.t_l1, "A1"))
        self.assertTrue(util.can_delegate_action(self.t_l3, self.t_l1, "C1"))

        # L2 -> L1: pode delegar B1 (delegable em L2) e A1 (delegable herdada de L1)
        self.assertTrue(util.can_delegate_action(self.t_l2, self.t_l1, "B1"))
        self.assertTrue(util.can_delegate_action(self.t_l2, self.t_l1, "A1"))
        # Não pode delegar A2 (não delegable) e nem algo que não exista
        self.assertFalse(util.can_delegate_action(self.t_l2, self.t_l1, "A2"))
        self.assertFalse(util.can_delegate_action(self.t_l2, self.t_l1, "NOPE"))

        # L1 -> L1: caminho proibido
        self.assertFalse(util.can_delegate_action(self.t_l1, self.t_l1, "A1"))
        # L1 -> L2: proibido
        self.assertFalse(util.can_delegate_action(self.t_l1, self.t_l2, "A1"))
        # L2 -> L3: proibido (só desce)
        self.assertFalse(util.can_delegate_action(self.t_l2, self.t_l3, "B1"))
