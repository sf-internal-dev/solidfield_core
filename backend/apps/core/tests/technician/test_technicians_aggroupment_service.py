# backend/apps/core/tests/technician/test_technicians_aggroupment_service.py

from django.test import TestCase
from unittest.mock import patch
from backend.apps.core.models import CompanyTenant, Technician, TechniciansAggroupment

from backend.apps.core.services import technicians_aggroupment_service as svc


class TechniciansAggroupmentServiceTest(TestCase):
    def setUp(self):
        print("→ setUp: criando tenant e técnicos")
        self.tenant = CompanyTenant.objects.create(name="TenantAGG", slug="tenant-agg")
        self.op = Technician.objects.create(
            tenant=self.tenant, username="op1", social_name="Operador", technician_permission="L3"
        )
        self.t1 = Technician.objects.create(
            tenant=self.tenant, username="t1", social_name="Tec 1", technician_permission="L1"
        )
        self.groupA = TechniciansAggroupment.objects.create(
            tenant=self.tenant, tag="A", allowed_to_operate=False
        )

    # -----------------------------
    # create_technicians_aggroupment
    # -----------------------------
    @patch("backend.apps.core.services.technicians_aggroupment_service.has_permission", return_value=(False, ["no_perm"]))
    def test_create_aggroupment_permission_denied(self, _mock_perm):
        print("✓ create_technicians_aggroupment: permissão negada → não cria")
        agg, errors = svc.create_technicians_aggroupment(technician=self.op, tenant=self.tenant)
        self.assertIsNone(agg)
        self.assertEqual(errors, ["no_perm"])
        self.assertEqual(TechniciansAggroupment.objects.count(), 1)  # só o A criado no setUp

    @patch("backend.apps.core.services.technicians_aggroupment_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technicians_aggroupment_service.define_aggroupment_tag", return_value="B")
    def test_create_aggroupment_success_uses_util_tag(self, _mock_def, _mock_perm):
        print("✓ create_technicians_aggroupment: cria com tag definida pelo util")
        agg, errors = svc.create_technicians_aggroupment(technician=self.op, tenant=self.tenant)
        self.assertEqual(errors, [])
        self.assertIsInstance(agg, TechniciansAggroupment)
        self.assertEqual(agg.tag, "B")
        self.assertEqual(agg.tenant, self.op.tenant)

    # -----------------------------
    # add_technician_to_aggroupment
    # -----------------------------
    @patch("backend.apps.core.services.technicians_aggroupment_service.has_permission", return_value=(False, ["no_perm"]))
    def test_add_technician_permission_denied_returns_error(self, _mock_perm):
        print("✓ add_technician_to_aggroupment: permissão negada → retorna erro")
        result = svc.add_technician_to_aggroupment(
            technician_operating=self.op, aggroupment=self.groupA, technician_to_add=self.t1
        )
        self.assertEqual(result, ["no_perm"])

    @patch("backend.apps.core.services.technicians_aggroupment_service.has_permission", return_value=(True, []))
    def test_add_technician_bug_short_circuit_on_empty_error_list(self, _mock_perm):
        print("✓ add_technician_to_aggroupment: BUG → retorna [] por causa de `error_p is not \"\"`")
        # Com ok=True e error_p=[], a função interrompe e retorna [] sem fazer nada
        result = svc.add_technician_to_aggroupment(
            technician_operating=self.op, aggroupment=self.groupA, technician_to_add=self.t1
        )
        self.assertEqual(result, [])  # documenta o bug atual

    @patch("backend.apps.core.services.technicians_aggroupment_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technicians_aggroupment_service.can_add_technician_to_aggroupment", return_value=(False, ["cannot_add"]))
    def test_add_technician_cannot_add_returns_error(self, _mock_can, _mock_perm):
        print("✓ add_technician_to_aggroupment: quando regra nega, retorna a lista de erros")
        result = svc.add_technician_to_aggroupment(
            technician_operating=self.op, aggroupment=self.groupA, technician_to_add=self.t1
        )
        self.assertEqual(result, ["cannot_add"])

    # -----------------------------
    # check_aggroupment_is_allowed_to_operate
    # -----------------------------
    @patch("backend.apps.core.services.technicians_aggroupment_service.has_permission", return_value=(False, ["no_perm"]))
    def test_check_allowed_permission_denied(self, _mock_perm):
        print("✓ check_aggroupment_is_allowed_to_operate: sem permissão → retorna erro")
        result = svc.check_aggroupment_is_allowed_to_operate(self.op, self.groupA)
        self.assertEqual(result, ["no_perm"])

    @patch("backend.apps.core.services.technicians_aggroupment_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technicians_aggroupment_service.allowed_aggroupment", return_value=True)
    def test_check_allowed_true_false_paths(self, _mock_allowed, _mock_perm):
        print("✓ check_aggroupment_is_allowed_to_operate: retorna bool conforme flag do grupo")
        # quando allowed_aggroupment=True e allowed_to_operate=True
        self.groupA.allowed_to_operate = True
        self.groupA.save(update_fields=["allowed_to_operate"])
        self.assertTrue(svc.check_aggroupment_is_allowed_to_operate(self.op, self.groupA))

        # quando allowed_aggroupment=True e allowed_to_operate=False
        self.groupA.allowed_to_operate = False
        self.groupA.save(update_fields=["allowed_to_operate"])
        self.assertFalse(svc.check_aggroupment_is_allowed_to_operate(self.op, self.groupA))

    @patch("backend.apps.core.services.technicians_aggroupment_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technicians_aggroupment_service.allowed_aggroupment", return_value=False)
    def test_check_allowed_returns_empty_error_list_bug(self, _mock_allowed, _mock_perm):
        print("✓ check_aggroupment_is_allowed_to_operate: BUG → quando regra nega, retorna []")
        # allowed_aggroupment=False cai no `return error` — mas `error` é [], logo retorna [] (inconsistência de tipo)
        result = svc.check_aggroupment_is_allowed_to_operate(self.op, self.groupA)
        self.assertEqual(result, [])  # documenta o bug atual
