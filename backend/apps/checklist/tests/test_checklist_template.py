# backend/apps/checklist/tests/test_checklist_template.py

from django.test import TestCase
from unittest.mock import patch

from backend.apps.core.models import CompanyTenant, Technician, TechniciansAggroupment
from backend.apps.checklist.models import ChecklistTemplate, ChecklistItemTemplate
from backend.apps.checklist.services import checklist_template_service as svc


class TemplateServiceTestCase(TestCase):
    def setUp(self):
        print("→ setUp: Criando tenant, técnico, aggroupment e template base")
        self.tenant = CompanyTenant.objects.create(name="TenantX", slug="tenant-x")

        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="techuser",
            social_name="Tech User",
            technician_permission="L1",
        )

        # ⚠️ TechniciansAggroupment exige tenant e usa 'tag' (não 'name')
        self.group = TechniciansAggroupment.objects.create(
            tenant=self.tenant,
            tag="A",
            allowed_to_operate=False,
        )

        self.template = ChecklistTemplate.objects.create(
            tenant=self.tenant,
            name="Template Instalação",
            version=1,
            created_by=self.tech,
            service_type="Instalação",
            is_active=True,
            is_global=True,
        )

    # -----------------------------
    # create_checklist_template
    # -----------------------------
    @patch("backend.apps.checklist.services.checklist_template_service.has_permission", return_value=(True, []))
    def test_create_checklist_template_success(self, _mock_perm):
        print("✓ create_checklist_template: cria template básico")
        tpl, errs = svc.create_checklist_template(
            technician_operating=self.tech,         # services do jeito que estão
            name="Novo Template",
            technician=self.tech,
            service_type="Reparo",
            is_global=False,
        )
        self.assertEqual(errs, [])
        self.assertIsInstance(tpl, ChecklistTemplate)
        self.assertEqual(tpl.name, "Novo Template")
        self.assertEqual(tpl.service_type, "Reparo")

    # -----------------------------
    # add_item_to_checklist_template
    # -----------------------------
    @patch("backend.apps.checklist.services.checklist_template_service.has_permission", return_value=(True, []))
    def test_add_item_success_and_conflict(self, _mock_perm):
        print("✓ add_item_to_checklist_template: adiciona item com ordem automática")
        item, errs = svc.add_item_to_checklist_template(
            technician_operating=self.tech,
            template=self.template,
            question="Pergunta 1",
            answer_type="text",
            is_required=True,
            choice_options="",
        )
        self.assertEqual(errs, [])
        self.assertIsInstance(item, ChecklistItemTemplate)
        self.assertEqual(item.order, 1)

        print("✓ add_item_to_checklist_template: detecta conflito de ordem")
        item2, errs2 = svc.add_item_to_checklist_template(
            technician_operating=self.tech,
            template=self.template,
            question="Pergunta 2",
            answer_type="text",
            is_required=True,
            choice_options="",
            order=1,  # força duplicado
        )
        self.assertIsNone(item2)
        self.assertTrue(any("already exists" in e for e in errs2))

    # -----------------------------
    # delegate_checklist_template_to_aggroupment
    # -----------------------------
    @patch("backend.apps.checklist.services.checklist_template_service.has_permission", return_value=(True, []))
    def test_delegate_to_aggroupment_global_becomes_specific(self, _mock_perm):
        print("✓ delegate_checklist_template_to_aggroupment: global → específico e associa grupo")
        tpl, errs = svc.delegate_checklist_template_to_aggroupment(
            technician_operating=self.tech,
            template=self.template,
            aggroupment=self.group,
        )
        self.assertEqual(errs, [])
        self.assertFalse(tpl.is_global)
        self.assertIn(self.group, tpl.aggroupments.all())

    # -----------------------------
    # remove_aggroupment_from_template
    # -----------------------------
    @patch("backend.apps.checklist.services.checklist_template_service.has_permission", return_value=(True, []))
    def test_remove_aggroupment_constraints(self, _mock_perm):
        print("✓ remove_aggroupment_from_template: não remove se for global")
        tpl, errs = svc.remove_aggroupment_from_template(
            technician_operating=self.tech,
            template=self.template,
            aggroupment=self.group,
        )
        self.assertEqual(errs, [])
        self.assertTrue(tpl.is_global)

        print("✓ remove_aggroupment_from_template: não deixa remover último grupo")
        self.template.is_global = False
        self.template.save()
        self.template.aggroupments.set([self.group])
        tpl2, errs2 = svc.remove_aggroupment_from_template(
            technician_operating=self.tech,
            template=self.template,
            aggroupment=self.group,
        )
        self.assertIsNone(tpl2)
        self.assertIn("would_violate_min_groups", errs2)

    # -----------------------------
    # update_checklist_template_version
    # -----------------------------
    @patch("backend.apps.checklist.services.checklist_template_service.has_permission", return_value=(True, []))
    def test_update_checklist_template_version_copy_and_remove(self, _mock_perm):
        print("✓ update_checklist_template_version: cria nova versão, copia itens, remove e adiciona")
        ChecklistItemTemplate.objects.create(
            template=self.template,
            order=1,
            question="Q1",
            answer_type="text",
            required=True,
        )

        new_tpl, errs = svc.update_checklist_template_version(
            technician_operating=self.tech,
            template=self.template,
            orders_to_remove=[999],  # inexistente
            items_to_add=[{"question": "Q2", "answer_type": "bool", "is_required": True}],
            copy_aggroupments=False,
            deactivate_previous=True,
        )
        self.assertIsInstance(new_tpl, ChecklistTemplate)
        self.assertTrue(any(e.startswith("item_not_found_by_order:") for e in errs))
        # original desativado
        self.template.refresh_from_db()
        self.assertFalse(self.template.is_active)
        # nova versão tem os itens esperados
        self.assertGreaterEqual(new_tpl.itens.count(), 2)
