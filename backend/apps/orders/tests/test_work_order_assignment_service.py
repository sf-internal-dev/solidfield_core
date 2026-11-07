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
        print("→ setUp: creating tenant, technicians, and work order")
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

        # in the current model, assigned_to is required (non-null)
        self.wo = WorkOrder.objects.create(
            tenant=self.tenant,
            identifier="TENA0001",
            created_by=self.tech_a,
            assigned_to=self.tech_a,
            status="open",
            work_start=None,
            work_end=None,
        )

    @patch("backend.apps.orders.services.work_order_assignment_service.log_work_order_reassignment")
    @patch("backend.apps.orders.services.work_order_assignment_service.log_work_order_assignment")
    def test_assign_same_technician_returns_true_and_logs_assignment(self, log_assign, log_reassign):
        print("✓ assign_work_order_to_technician: same technician → returns True, does not change assigned_to, logs assignment")
        result = assign_work_order_to_technician(self.wo, self.tech_a)

        # returns True (because assigned_to == technician)
        self.assertTrue(result)
        # does NOT change the assignee (current behavior)
        self.wo.refresh_from_db()
        self.assertEqual(self.wo.assigned_to_id, self.tech_a.id)

        # logs: with assigned_to already set, the service calls log_work_order_assignment
        log_assign.assert_called_once_with(work_order=self.wo, technician=self.tech_a, tenant=self.tenant)
        log_reassign.assert_not_called()

    @patch("backend.apps.orders.services.work_order_assignment_service.log_work_order_reassignment")
    @patch("backend.apps.orders.services.work_order_assignment_service.log_work_order_assignment")
    def test_assign_different_technician_returns_false_and_does_not_change_assigned(self, log_assign, log_reassign):
        print("✓ assign_work_order_to_technician: different technician → returns False, does not change assigned_to, logs assignment (BUG: does not reassign)")
        result = assign_work_order_to_technician(self.wo, self.tech_b)

        # returns False (because assigned_to != technician)
        self.assertFalse(result)
        # assigned_to stays the same (BUG: service does not update it)
        self.wo.refresh_from_db()
        self.assertEqual(self.wo.assigned_to_id, self.tech_a.id)

        # still logs assignment, not reassignment (documenting the current behavior)
        log_assign.assert_called_once_with(work_order=self.wo, technician=self.tech_b,tenant=self.tenant )
        log_reassign.assert_not_called()

    @patch("backend.apps.orders.services.work_order_assignment_service.log_work_order_reassignment")
    @patch("backend.apps.orders.services.work_order_assignment_service.log_work_order_assignment")
    def test_never_hits_else_branch_given_assigned_to_is_non_null(self, log_assign, log_reassign):
        print("✓ assign_work_order_to_technician: 'else' branch is unreachable because assigned_to is required (non-null)")
        # In the current model the assigned_to field is required, so it always falls into the if.
        _ = assign_work_order_to_technician(self.wo, self.tech_b)
        log_assign.assert_called()   # called at least once
        log_reassign.assert_not_called()
