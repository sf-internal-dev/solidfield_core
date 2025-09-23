# backend/apps/core/tests/test_permission_utils.py

from django.test import TestCase
from unittest.mock import patch

from backend.apps.core.models import CompanyTenant, Technician
# ⬇️ ajuste este import para o caminho REAL do seu módulo de funções:
from backend.apps.core.utils.technician_permission import technician_permission_delegation_util as util


class PermissionUtilsPatchedSchemaTest(TestCase):
    def setUp(self):
        print("→ setUp: criando tenant e técnicos L1/L3")
        self.tenant = CompanyTenant.objects.create(name="TenantPerm", slug="tenant-perm")

        self.t_l1 = Technician.objects.create(
            tenant=self.tenant, username="l1", social_name="Tec L1", technician_permission="L1"
        )
        self.t_l3 = Technician.objects.create(
            tenant=self.tenant, username="l3", social_name="Tec L3", technician_permission="L3"
        )

        # Schema de teste controlado (não depende do schema real de produção)
        self.TEST_SCHEMA = {
            "L1": {
                "label": "Execution (Field Level)",
                "actions": [
                    {"code": "A1", "label": "Action 1"},
                    {"code": "A2", "label": "Action 2"},
                ],
                # sem herança
            },
            "L2": {
                "label": "Coordination (Local Supervision)",
                "actions": [
                    {"code": "B1", "label": "Action B1"},
                ],
                # herda SELETIVAMENTE SÓ A1 de L1
                "inherits_selectively_from": {
                    "L1": ["A1"],
                },
            },
            "L3": {
                "label": "Full Control (Operational Management)",
                "actions": [
                    {"code": "C1", "label": "Action C1"},
                ],
                # herda SELETIVAMENTE B1 de L2 (e via recursão também trará A1)
                "inherits_selectively_from": {
                    "L2": ["B1"],
                },
            },
            # nível cíclico para testar proteção de 'visited'
            "CYCLE": {
                "label": "Cycle",
                "actions": [],
                "inherits_selectively_from": {
                    "CYCLE": ["A1"],  # auto-referência
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
        print("✓ delegate_complete_permission_level: L3 pode delegar, L1 não pode")
        # L3 delega: deve alterar o nível do L1 para L2
        ok = util.delegate_complete_permission_level(self.t_l3, self.t_l1, "L2")
        self.assertTrue(ok)
        self.t_l1.refresh_from_db()
        self.assertEqual(self.t_l1.technician_permission, "L2")

        # L1 tenta delegar: deve falhar e não alterar
        ok2 = util.delegate_complete_permission_level(self.t_l1, self.t_l3, "L1")
        self.assertFalse(ok2)
        self.t_l3.refresh_from_db()
        self.assertEqual(self.t_l3.technician_permission, "L3")

    # -----------------------------
    # get_effective_actions_for_level
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_get_effective_actions_for_level_selective_and_recursive(self, mock_schema):
        print("✓ get_effective_actions_for_level: herança seletiva + recursão sem loop")
        # injeta schema fake
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # L1: apenas suas ações
        a_l1 = set(util.get_effective_actions_for_level("L1"))
        self.assertEqual(a_l1, {"A1", "A2"})

        # L2: suas ações + seletivas de L1 (A1)
        a_l2 = set(util.get_effective_actions_for_level("L2"))
        self.assertEqual(a_l2, {"B1", "A1", "A2"})

        # L3: suas ações + B1 de L2 + (via recursão) A1 de L1
        a_l3 = set(util.get_effective_actions_for_level("L3"))
        self.assertEqual(a_l3, {"C1", "B1", "A1", "A2"})

        # nível com ciclo: não deve travar nem duplicar infinitamente
        a_cycle = set(util.get_effective_actions_for_level("CYCLE"))
        self.assertIn("A1", a_cycle)  # veio do próprio mapeamento seletivo
        # nada além disso, já que não há ações próprias nem outros ramos

    # -----------------------------
    # get_effective_action_objects_for_level
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_get_effective_action_objects_for_level_strict_selective(self, mock_schema):
        print("✓ get_effective_action_objects_for_level: respeita seleção por código do nível atual")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # Para L2: objetos de B1 (próprio) + A1 (herdado seletivamente de L1)
        objs_l2 = util.get_effective_action_objects_for_level("L2")
        codes_l2 = {o["code"] for o in objs_l2}
        self.assertEqual(codes_l2, {"B1", "A1"})
        labels_l2 = {o["label"] for o in objs_l2}
        self.assertIn("Action B1", labels_l2)
        self.assertIn("Action 1", labels_l2)
        self.assertNotIn("Action 2", labels_l2)  # A2 não foi listado na herança

        # Para L3: objetos de C1 (próprio) + B1 (herdado de L2)
        # (A1 não entra aqui porque L3 não o listou na herança do nível imediatamente herdado)
        objs_l3 = util.get_effective_action_objects_for_level("L3")
        codes_l3 = {o["code"] for o in objs_l3}
        self.assertEqual(codes_l3, {"C1", "B1"})

    # -----------------------------
    # get_action_label
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_get_action_label(self, mock_schema):
        print("✓ get_action_label: encontra o label correto via objetos efetivos")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        self.assertEqual(util.get_action_label("L2", "A1"), "Action 1")
        self.assertIsNone(util.get_action_label("L2", "A2"))  # não herdado por L2

    # -----------------------------
    # technician_has_permission_for_action
    # -----------------------------
    @patch.object(util, "ACTIONS_BY_PERMISSION_SCHEMA")
    def test_technician_has_permission_for_action(self, mock_schema):
        print("✓ technician_has_permission_for_action: usa conjunto efetivo do nível do técnico")
        mock_schema.get.side_effect = self.TEST_SCHEMA.get
        mock_schema.__getitem__.side_effect = self.TEST_SCHEMA.__getitem__
        mock_schema.__contains__.side_effect = self.TEST_SCHEMA.__contains__

        # após delegação, L1 -> L2
        ok = util.delegate_complete_permission_level(self.t_l3, self.t_l1, "L2")
        self.assertTrue(ok)
        self.t_l1.refresh_from_db()
        self.assertEqual(self.t_l1.technician_permission, "L2")

        # L2 deve ter B1 e A1, mas não A2
        self.assertTrue(util.technician_has_permission_for_action(self.t_l1, "B1"))
        self.assertTrue(util.technician_has_permission_for_action(self.t_l1, "A1"))
        self.assertTrue(util.technician_has_permission_for_action(self.t_l1, "A2"))
