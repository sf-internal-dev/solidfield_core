# backend/apps/checklist/tests/test_checklist_service.py

from django.test import TestCase
from unittest.mock import patch
from types import SimpleNamespace

from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.checklist.models import (
    ChecklistTemplate,
    ChecklistItemTemplate,
    Checklist,
    ChecklistItemAnswer,
)
# ajuste este import pro caminho real do módulo que contém as funções abaixo
from backend.apps.checklist.services import checklist_service as svc


class ChecklistServiceTestCase(TestCase):
    def setUp(self):
        print("→ setUp: Criando tenant, técnico(s), template e checklist base")
        self.tenant = CompanyTenant.objects.create(name="TenantCS", slug="tenant-cs")

        self.tech_op = Technician.objects.create(
            tenant=self.tenant, username="op", social_name="Operador", technician_permission="L1"
        )
        self.tech_filled = Technician.objects.create(
            tenant=self.tenant, username="filled", social_name="Preenchedor", technician_permission="L1"
        )

        self.tpl = ChecklistTemplate.objects.create(
            tenant=self.tenant,
            name="Template SV",
            version=1,
            created_by=self.tech_op,
            service_type="Serviço",
            is_active=True,
            is_global=True,
        )

        # checklist simples (vai ser usado em vários testes)
        self.checklist = Checklist.objects.create(
            template=self.tpl,
            filled_by=self.tech_filled,
            status="draft",
            incomplete=True,
        )

    # -----------------------------
    # create_checklist
    # -----------------------------
    @patch("backend.apps.checklist.services.checklist_service.has_permission", return_value=(True, []))
    def test_create_checklist_success(self, _mock_perm):
        print("✓ create_checklist: cria com permissões ok")
        cl, errs = svc.create_checklist(
            technician_operating=self.tech_op, template=self.tpl, filled_by=self.tech_filled
        )
        self.assertEqual(errs, [])
        self.assertIsInstance(cl, Checklist)
        self.assertEqual(cl.template, self.tpl)
        self.assertEqual(cl.filled_by, self.tech_filled)

    # -----------------------------
    # save_answer
    # -----------------------------
    @patch("backend.apps.checklist.services.checklist_service.has_permission", return_value=(True, []))
    def test_save_answer_bool_ok(self, _mock_perm):
        print("✓ save_answer: bool required com True/False explícito")
        it = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=1, question="Funciona?", answer_type="bool", required=True
        )
        ans, errs = svc.save_answer(
            technician_operating=self.tech_op, checklist=self.checklist, item_template=it, value=True
        )
        self.assertEqual(errs, [])
        self.assertIsInstance(ans, ChecklistItemAnswer)
        self.assertIs(ans.answer_bool, True)
        self.assertIsNone(ans.answer_texto)
        self.assertIsNone(ans.answer_number)
        self.assertIsNone(ans.answer_choice)

    @patch("backend.apps.checklist.services.checklist_service.has_permission", return_value=(True, []))
    def test_save_answer_required_missing_text(self, _mock_perm):
        print("✓ save_answer: required text vazio → required_value_missing")
        it = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=2, question="Descreva", answer_type="text", required=True
        )
        ans, errs = svc.save_answer(
            technician_operating=self.tech_op, checklist=self.checklist, item_template=it, value="   "
        )
        self.assertIsNone(ans)
        self.assertIn("required_value_missing", errs)

    @patch("backend.apps.checklist.services.checklist_service.has_permission", return_value=(True, []))
    def test_save_answer_choice_not_in_options(self, _mock_perm):
        print("✓ save_answer: choice fora das opções → choice_not_in_options")
        it = ChecklistItemTemplate.objects.create(
            template=self.tpl,
            order=3,
            question="Escolha",
            answer_type="choice",
            required=True,
            choice_options="A,B,C",
        )
        ans, errs = svc.save_answer(
            technician_operating=self.tech_op, checklist=self.checklist, item_template=it, value="D"
        )
        self.assertIsNone(ans)
        self.assertIn("choice_not_in_options", errs)

    # -----------------------------
    # remove_answer
    # -----------------------------
    @patch("backend.apps.checklist.services.checklist_service.has_permission", return_value=(True, []))
    def test_remove_answer_ok_and_not_found(self, _mock_perm):
        print("✓ remove_answer: remove existente e lida com inexistente")
        it = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=4, question="Remover?", answer_type="bool", required=False
        )
        # cria uma resposta para remover
        a = ChecklistItemAnswer.objects.create(checklist=self.checklist, item_template=it, answer_bool=False)
        ok, errs = svc.remove_answer(
            technician_operating=self.tech_op, checklist=self.checklist, item_template=it
        )
        self.assertTrue(ok)
        self.assertEqual(errs, [])
        # tentar remover de novo → not found
        ok2, errs2 = svc.remove_answer(
            technician_operating=self.tech_op, checklist=self.checklist, item_template=it
        )
        self.assertFalse(ok2)
        self.assertIn("item_answer_not_found", errs2)

    # -----------------------------
    # list_missing_required_answers
    # -----------------------------
    def test_list_missing_required_answers_basic(self):
        print("✓ list_missing_required_answers: identifica itens obrigatórios sem resposta")
        it_bool = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=5, question="B?", answer_type="bool", required=True
        )
        it_text = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=6, question="T?", answer_type="text", required=True
        )
        it_opt = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=7, question="Opcional", answer_type="text", required=False
        )
        # responde só o bool
        ChecklistItemAnswer.objects.create(checklist=self.checklist, item_template=it_bool, answer_bool=False)

        missing, errs = svc.list_missing_required_answers(checklist=self.checklist)
        self.assertEqual(errs, [])
        # deve faltar o de texto (obrigatório) e não listar o opcional
        self.assertIn(it_text.id, missing)
        self.assertNotIn(it_bool.id, missing)
        self.assertNotIn(it_opt.id, missing)

    # -----------------------------
    # bulk_save_answers
    # -----------------------------
    @patch("backend.apps.checklist.services.checklist_service.has_permission", return_value=(True, []))
    def test_bulk_save_answers_ok_not_found_and_error_bubbling(self, _mock_perm):
        print("✓ bulk_save_answers: salva vários, acumula erros e ignora inexistentes")

        # itens de template
        it1 = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=10, question="Q1", answer_type="bool", required=True
        )
        it2 = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=11, question="Q2", answer_type="choice", required=True, choice_options="X,Y"
        )

        saved, errs = svc.bulk_save_answers(
            technician_operating=self.tech_op,
            checklist=self.checklist,
            payloads=[
                {"item_template": it1.id, "value": True},
                {"item_template": it2.id, "value": "Z"},
                {"item_template": 999999, "value": "whatever"},
            ],
        )

        # verificações
        self.assertTrue(any(isinstance(a, ChecklistItemAnswer) for a in saved))
        # deve ter erro por item_template_not_found e choice_not_in_options
        self.assertIn("item_template_not_found", errs)
        self.assertIn("choice_not_in_options", errs)
        # garantia de que salvou o primeiro
        self.assertTrue(ChecklistItemAnswer.objects.filter(checklist=self.checklist, item_template=it1).exists())
