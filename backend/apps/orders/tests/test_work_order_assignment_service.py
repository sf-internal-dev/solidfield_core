# backend/apps/orders/tests/test_work_order_assignment_service.py

from django.test import TestCase
from unittest.mock import patch

from django.utils import timezone
from backend.apps.core.models import CompanyTenant
from backend.apps.core.models.technician import Technician
from backend.apps.orders.models.work_order import WorkOrder
from backend.apps.orders.services.work_order_assignment_service import (
    assign_work_order_to_technician,
)


class WorkOrderAssignmentServiceTest(TestCase):
    def setUp(self):
        print("→ setUp: criando tenant, técnicos e ordem de serviço")
        self.tenant = CompanyTenant.objects.create(name="Tenant A", slug="tena", tenant_code="TENA")

        self.tech_a = Technician.objects.create(
            tenant=self.tenant,
            username="techA",
            social_name="Tech A",
            technician_permission="L3",
            is_active=True,
        )
        self.tech_b = Technician.objects.create(
            tenant=self.tenant,
            username="techB",
            social_name="Tech B",
            technician_permission="L3",
            is_active=True,
        )

        # no modelo atual, assigned_to é obrigatório (não-nulo)
        self.wo = WorkOrder.objects.create(
            tenant=self.tenant,
            identifier="TENA0001",
            created_by=self.tech_a,
            assigned_to=self.tech_a,
            status="open",
            work_start=None,
            work_end=None,
        )

    @patch("backend.apps.core.services.audition_log_service.log_work_order_reassignment")
    @patch("backend.apps.core.services.audition_log_service.log_work_order_assignment")
    def test_assign_same_technician_returns_true_and_logs_assignment(self, log_assign, log_reassign):
        print("✓ assign_work_order_to_technician: mesmo técnico → retorna True, não altera assigned_to, loga assignment")
        result = assign_work_order_to_technician(self.wo, self.tech_a)

        # retorno True (porque assigned_to == technician)
        self.assertTrue(result)
        # NÃO altera o responsável (comportamento atual)
        self.wo.refresh_from_db()
        self.assertEqual(self.wo.assigned_to_id, self.tech_a.id)

        # logs: com assigned_to já preenchido, service chama log_work_order_assignment
        log_assign.assert_called_once_with(work_order=self.wo, technician=self.tech_a)
        log_reassign.assert_not_called()

    @patch("backend.apps.core.services.audition_log_service.log_work_order_reassignment")
    @patch("backend.apps.core.services.audition_log_service.log_work_order_assignment")
    def test_assign_different_technician_returns_false_and_does_not_change_assigned(self, log_assign, log_reassign):
        print("✓ assign_work_order_to_technician: técnico diferente → retorna False, não altera assigned_to, loga assignment (BUG de não reatribuir)")
        result = assign_work_order_to_technician(self.wo, self.tech_b)

        # retorno False (porque assigned_to != technician)
        self.assertFalse(result)
        # assigned_to permanece o mesmo (BUG: service não atualiza)
        self.wo.refresh_from_db()
        self.assertEqual(self.wo.assigned_to_id, self.tech_a.id)

        # ainda assim loga assignment, não reassignment (documentando o comportamento atual)
        log_assign.assert_called_once_with(work_order=self.wo, technician=self.tech_b)
        log_reassign.assert_not_called()

    @patch("backend.apps.core.services.audition_log_service.log_work_order_reassignment")
    @patch("backend.apps.core.services.audition_log_service.log_work_order_assignment")
    def test_never_hits_else_branch_given_assigned_to_is_non_null(self, log_assign, log_reassign):
        print("✓ assign_work_order_to_technician: ramo 'else' é inalcançável porque assigned_to é obrigatório (não-nulo)")
        # No modelo atual o campo assigned_to é obrigatório; então sempre cairá no if.
        _ = assign_work_order_to_technician(self.wo, self.tech_b)
        log_assign.assert_called()   # chamado ao menos uma vez
        log_reassign.assert_not_called()
