from django.test import TestCase
from django.utils import timezone
from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.orders.models import ServiceOrder
from backend.apps.checklist.models import (
    ChecklistTemplate,
    ChecklistItemTemplate,
    Checklist,
    ChecklistItemAnswer
)
from backend.apps.clients.models import Client
from django.core.exceptions import ValidationError

class ChecklistModelsTestCase(TestCase):
    def setUp(self):
        print("→ setUp: Creating tenant, technician, work order, and base template for the checklist...")
        self.tenant = CompanyTenant.objects.create(name="TenantChecklist", slug="tenant-check")
        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="checktech",
            social_name="Check Tech",
            technician_permission="L1"
        )
        self.client = Client.objects.create(
            tenant=self.tenant,
            person_type="company",
            name="Fictional Client",
            document_id="1234567890001",
            contact_name="João da Silva",
            phone="(11) 99999-9999",
            email="client@example.com"
        )

        self.order = ServiceOrder.objects.create(
            tenant=self.tenant,
            identifier="OS001",
            created_by=self.tech,
            assigned_to=self.tech,
            client=self.client # can be mocked with a fake client if needed
        )
        self.template = ChecklistTemplate.objects.create(
            tenant=self.tenant,
            name="Standard Installation",
            version=1,
            created_by=self.tech,
            service_type="Installation"
        )

    def test_template_str(self):
        print("✓ test_template_str: __str__ should show name, version, and type")
        self.assertEqual(str(self.template), "Standard Installation v1 (Installation)")

    def test_item_template_creation_and_str(self):
        print("✓ test_item_template_creation_and_str: Creating an item with a long question")
        item = ChecklistItemTemplate.objects.create(
            template=self.template,
            order=1,
            question="This is a very long question that should be cut off in the string representation",
            answer_type="bool"
        )
        self.assertIn("1. This is a very long question", str(item))

    def test_checklist_creation_and_str(self):
        print("✓ test_checklist_creation_and_str: Creating a checklist linked to a work order")
        checklist = Checklist.objects.create(
            service_order=self.order,
            template=self.template,
            filled_by=self.tech
        )
        self.assertIn("Checklist #", str(checklist))
        self.assertIn("OS001", str(checklist))

    def test_answer_bool_valid(self):
        print("✓ test_answer_bool_valid: Creating a valid boolean answer")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=1, question="Is it working?", answer_type="bool")
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item, answer_bool=True)
        answer.clean()
        self.assertTrue(answer.answer_bool)

    def test_answer_bool_invalid(self):
        print("✓ test_answer_bool_invalid: Should fail if the bool answer is None")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=1, question="Bool question", answer_type="bool")
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item)
        with self.assertRaises(ValidationError):
            answer.clean()

    def test_answer_text_required(self):
        print("✓ test_answer_text_required: Should fail if the text is blank")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=2, question="Describe...", answer_type="text")
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item, answer_texto="")
        with self.assertRaises(ValidationError):
            answer.clean()

    def test_answer_choice_required(self):
        print("✓ test_answer_choice_required: Should fail if the choice is not provided")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=3, question="Which option?", answer_type="choice")
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item)
        with self.assertRaises(ValidationError):
            answer.clean()

    def test_answer_numeric_required(self):
        print("✓ test_answer_numeric_required: Should fail if a required numeric field is empty")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=4, question="Temperature", answer_type="temperature", required=True)
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item)
        with self.assertRaises(ValidationError):
            answer.clean()

    def test_answer_numeric_optional(self):
        print("✓ test_answer_numeric_optional: Should accept an empty numeric value if 'required=False'")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=5, question="Height", answer_type="height_cm", required=False)
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item)
        answer.clean()  # should not raise an exception
