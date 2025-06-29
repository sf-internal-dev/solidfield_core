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
        print("→ setUp: Criando tenant, técnico, OS e template base para checklist...")
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
            name="Cliente Fictício",
            document_id="1234567890001",
            contact_name="João da Silva",
            phone="(11) 99999-9999",
            email="cliente@exemplo.com"
        )

        self.order = ServiceOrder.objects.create(
            tenant=self.tenant,
            identifier="OS001",
            created_by=self.tech,
            assigned_to=self.tech,
            client=self.client # pode ser mockado com um cliente fake se necessário
        )
        self.template = ChecklistTemplate.objects.create(
            tenant=self.tenant,
            name="Instalação Padrão",
            version=1,
            created_by=self.tech,
            service_type="Instalação"
        )

    def test_template_str(self):
        print("✓ test_template_str: __str__ deve mostrar nome, versão e tipo")
        self.assertEqual(str(self.template), "Instalação Padrão v1 (Instalação)")

    def test_item_template_creation_and_str(self):
        print("✓ test_item_template_creation_and_str: Criando item com pergunta longa")
        item = ChecklistItemTemplate.objects.create(
            template=self.template,
            order=1,
            question="Esta é uma pergunta muito longa que deve ser cortada na representação em string",
            answer_type="bool"
        )
        self.assertIn("1. Esta é uma pergunta muito longa", str(item))

    def test_checklist_creation_and_str(self):
        print("✓ test_checklist_creation_and_str: Criando checklist vinculado a OS")
        checklist = Checklist.objects.create(
            service_order=self.order,
            template=self.template,
            filled_by=self.tech
        )
        self.assertIn("Checklist #", str(checklist))
        self.assertIn("OS001", str(checklist))

    def test_answer_bool_valid(self):
        print("✓ test_answer_bool_valid: Criando resposta booleana válida")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=1, question="Está funcionando?", answer_type="bool")
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item, answer_bool=True)
        answer.clean()
        self.assertTrue(answer.answer_bool)

    def test_answer_bool_invalid(self):
        print("✓ test_answer_bool_invalid: Deve falhar se resposta bool for None")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=1, question="Pergunta bool", answer_type="bool")
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item)
        with self.assertRaises(ValidationError):
            answer.clean()

    def test_answer_text_required(self):
        print("✓ test_answer_text_required: Deve falhar se texto estiver em branco")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=2, question="Descreva...", answer_type="text")
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item, answer_texto="")
        with self.assertRaises(ValidationError):
            answer.clean()

    def test_answer_choice_required(self):
        print("✓ test_answer_choice_required: Deve falhar se escolha não for fornecida")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=3, question="Qual opção?", answer_type="choice")
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item)
        with self.assertRaises(ValidationError):
            answer.clean()

    def test_answer_numeric_required(self):
        print("✓ test_answer_numeric_required: Deve falhar se campo numérico requerido estiver vazio")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=4, question="Temperatura", answer_type="temperature", required=True)
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item)
        with self.assertRaises(ValidationError):
            answer.clean()

    def test_answer_numeric_optional(self):
        print("✓ test_answer_numeric_optional: Deve aceitar numérico vazio se 'required=False'")
        checklist = Checklist.objects.create(service_order=self.order, template=self.template, filled_by=self.tech)
        item = ChecklistItemTemplate.objects.create(template=self.template, order=5, question="Altura", answer_type="height_cm", required=False)
        answer = ChecklistItemAnswer(checklist=checklist, item_template=item)
        answer.clean()  # não deve lançar exceção
