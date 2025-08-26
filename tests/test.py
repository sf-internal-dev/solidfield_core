from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from unittest.mock import patch
from backend.apps.core.models import AccountHolderUser, CompanyTenant, Technician, PermissionLevel, PermissionFlag, TemporaryDelegation
from backend.apps.clients.models import Client, ClientAddress
from backend.apps.orders.models import ServiceOrder
from backend.apps.checklist.models import Checklist, ChecklistItemAnswer, ChecklistItemTemplate, ChecklistTemplate
from backend.apps.filehub.models import ServiceOrderSignature
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from unittest.mock import patch
from backend.common.work_order_status_workflow import get_workflow_for_tenant, has_permission_for_status
class AllModelsTestCase(TestCase):
    def setUp(self):
        print("→ setUp: Criando dados de teste...")
        self.tenant = CompanyTenant.objects.create(name="TenantX", slug="tenantx")
        self.owner = AccountHolderUser.objects.create_user(email="owner@example.com", full_name="Owner")
        self.tenant.owner = self.owner
        self.tenant.save()
        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="tech1",
            social_name="Tech One",
            technician_permission=PermissionLevel.L1
        )
        self.client = Client.objects.create(tenant=self.tenant, name="Client A")
        self.order = ServiceOrder.objects.create(
            tenant=self.tenant,
            identifier="OS001",
            created_by=self.tech,
            assigned_to=self.tech,
            client=self.client
        )

    def test_account_holder_user_str(self):
        print("✓ test_account_holder_user_str")
        self.assertEqual(str(self.owner), self.owner.email)

    def test_company_tenant_str(self):
        print("✓ test_company_tenant_str")
        self.assertEqual(str(self.tenant), "TenantX")

    def test_technician_str(self):
        print("✓ test_technician_str")
        self.assertEqual(str(self.tech), "Tech One (tech1)")

    def test_permission_flag_unique(self):
        print("✓ test_permission_flag_unique")
        PermissionFlag.objects.create(level="L1", action="edit", allowed=True)
        with self.assertRaises(Exception):
            PermissionFlag.objects.create(level="L1", action="edit", allowed=False)

    def test_temporary_delegation_active(self):
        print("✓ test_temporary_delegation_active")
        now = timezone.now()
        now = timezone.now()
        delegation = TemporaryDelegation.objects.create(
            tenant=self.tenant,
            from_user=self.tech,
            to_user=self.tech,
            valid_from=now - timedelta(minutes=1),
            valid_until=now + timedelta(minutes=1)
        )
        self.assertTrue(delegation.is_active())


    def test_checklist_item_answer_clean(self):
        print("✓ test_checklist_item_answer_clean")
        template = ChecklistTemplate.objects.create(
            tenant=self.tenant,
            name="Template",
            version=1,
            created_by=self.tech,
            service_type="Test"
        )
        item = ChecklistItemTemplate.objects.create(
            template=template,
            order=1,
            question="Pergunta?",
            answer_type="bool"
        )
        checklist = Checklist.objects.create(
            service_order=self.order,
            template=template,
            filled_by=self.tech
        )
        answer = ChecklistItemAnswer(
            checklist=checklist,
            item_template=item,
            answer_bool=True
        )
        answer.clean()
        self.assertTrue(answer.answer_bool)

    def test_service_order_signature_creation(self):
        print("✓ test_service_order_signature_creation")
        signature = ServiceOrderSignature.objects.create(
            service_order=self.order,
            ordered_by=self.tech,
            signed_by="Cliente",
            image="signatures/test.png"
        )
        self.assertEqual(signature.signed_by, "Cliente")

    def test_client_address_str(self):
        print("✓ test_client_address_str")
        address = ClientAddress.objects.create(
            client=self.client,
            label="Matriz",
            street="Rua A",
            number="123",
            neighborhood="Centro",
            city="Cidade",
            state="SP",
            zip_code="00000-000"
        )
        self.assertIn("Matriz", str(address))


    # def test_service_order_status_update_valid(self):
    #     print("✓ test_service_order_status_update_valid")
    #     with patch("backend.apps.orders.models.get_workflow_for_tenant") as get_workflow, \
    #          patch("backend.apps.orders.models.has_permission_for_status") as has_permission:
    #         get_workflow.return_value = {"transitions": [{"from": "open", "to": "in_progress"}]}
    #         has_permission.return_value = True
    #         self.order.update_status(user=self.tech, new_status="in_progress")
    #         self.assertEqual(self.order.status, "in_progress")

    # def test_service_order_status_update_invalid(self):
    #     print("✓ test_service_order_status_update_invalid")
    #     with patch("backend.core.models.get_workflow_for_tenant") as get_workflow, \
    #          patch("backend.core.models.has_permission_for_status") as has_permission:
    #         get_workflow.return_value = {"transitions": [{"from": "open", "to": "finished"}]}
    #         has_permission.return_value = False
    #         with self.assertRaises(ValidationError):
    #             self.order.update_status(user=self.tech, new_status="finished")

