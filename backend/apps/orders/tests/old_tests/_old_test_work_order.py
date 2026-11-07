from django.test import TestCase
from unittest.mock import patch
from django.utils import timezone
from django.core.exceptions import ValidationError
from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.clients.models import Client
from backend.apps.orders.models import WorkOrder, WorkOrderDownloadLink

class WorkOrderModelTest(TestCase):
    def setUp(self):
        print("→ setUp: Creating tenant, technician, and client for a work order...")
        self.tenant = CompanyTenant.objects.create(name="TenantOS", slug="tenant-os")

        self.tech_creator = Technician.objects.create(
            tenant=self.tenant,
            username="tech_creator",
            social_name="Creator",
            technician_permission="L3"
        )
        self.tech_assigned = Technician.objects.create(
            tenant=self.tenant,
            username="tech_exec",
            social_name="Assignee",
            technician_permission="L1"
        )

        self.client = Client.objects.create(
            tenant=self.tenant,
            name="Work Order Client",
            person_type="company",
            document_id="9876543210001"
        )

        self.order = WorkOrder.objects.create(
            tenant=self.tenant,
            identifier="OS-2024-001",
            created_by=self.tech_creator,
            assigned_to=self.tech_assigned,
            client=self.client,
            client_name="John Doe",
            client_email="client@test.com",
            client_phone="(11) 99999-8888"
        )

    def test_str_representation(self):
        print("✓ test_str_representation: __str__ should return the identifier and the status")
        self.assertEqual(
            str(self.order),
            "Work Order #OS-2024-001 - Open"
        )

    def test_timestamps_are_auto(self):
        print("✓ test_timestamps_are_auto: created_at and updated_at should be filled in automatically")
        self.assertIsNotNone(self.order.created_at)
        self.assertIsNotNone(self.order.updated_at)
        self.assertLessEqual(self.order.created_at, timezone.now())

    @patch("backend.apps.core.utils.status_workflow.status_workflow_label_util.get_workflow_for_tenant")
    # @patch("backend.apps.core.utils.status_workflow.status_workflow_control_util.has_permission_for_status")
    def test_valid_status_transition(self, mock_has_permission):
        print("✓ test_valid_status_transition: Should allow a valid status change")

        # mock_get_workflow.return_value = {
        #     "transitions": [{"from": "open", "to": "in_progress"}]
        # }
        mock_has_permission.return_value = True

        self.order.update_status(user=self.tech_creator, new_status="in_progress")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "in_progress")
        self.assertTrue(any(entry["to"] == "in_progress" for entry in self.order.status_history))

    @patch("backend.apps.core.utils.status_workflow.status_workflow_label_util.get_workflow_for_tenant")
    # @patch("backend.apps.core.utils.status_workflow.status_workflow_control_util.has_permission_for_status")
    def test_invalid_status_transition_raises(self, mock_has_permission):
        print("✓ test_invalid_status_transition_raises: Should raise ValidationError if the transition is invalid")

        # mock_get_workflow.return_value = {
        #     "transitions": [{"from": "open", "to": "finished"}]
        # }
        mock_has_permission.return_value = False

        with self.assertRaises(ValidationError):
            self.order.status(user=self.tech_assigned, new_status="finished")

# class WorkOrderDocumentTest(TestCase):
#     def setUp(self):
#         print("→ setUp: Creating a work order for a generated PDF...")
#         self.tenant = CompanyTenant.objects.create(name="TenantDoc", slug="tenant-doc")
#         self.tech = Technician.objects.create(
#             tenant=self.tenant,
#             username="tech_doc",
#             social_name="Generator",
#             technician_permission="L2"
#         )
#         self.client = Client.objects.create(
#             tenant=self.tenant,
#             name="PDF Client",
#             person_type="individual",
#             document_id="1122334455"
#         )
#         self.order = WorkOrder.objects.create(
#             tenant=self.tenant,
#             identifier="OS-PDF-001",
#             created_by=self.tech,
#             assigned_to=self.tech,
#             client=self.client
#         )

    # def test_service_order_document_creation(self):
    #     print("✓ test_service_order_document_creation: Creating a PDF document linked to the order")
    #     doc = .objects.create(
    #         service_order=self.order,
    #         file="service_orders/pdfs/test.pdf",
    #         generated_by=self.tech
    #     )
    #     self.assertEqual(doc.file.name, "service_orders/pdfs/test.pdf")
    #     self.assertEqual(doc.generated_by, self.tech)
    #     self.assertIsNotNone(doc.generated_at)
    #     self.assertIn("PDF", str(doc))
