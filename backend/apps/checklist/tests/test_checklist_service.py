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
# adjust this import to the real path of the module that contains the functions below
from backend.apps.checklist.services import checklist_service as svc


class ChecklistServiceTestCase(TestCase):
    def setUp(self):
        print("→ setUp: Creating tenant, technician(s), template, and base checklist")
        self.tenant = CompanyTenant.objects.create(name="TenantCS", slug="tenant-cs")

        self.tech_op = Technician.objects.create(
            tenant=self.tenant, username="op", social_name="Operator", technician_permission="L1"
        )
        self.tech_filled = Technician.objects.create(
            tenant=self.tenant, username="filled", social_name="Filler", technician_permission="L1"
        )

        self.tpl = ChecklistTemplate.objects.create(
            tenant=self.tenant,
            name="Template SV",
            version=1,
            created_by=self.tech_op,
            service_type="Service",
            is_active=True,
            is_global=True,
        )

        # simple checklist (used in several tests)
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
        print("✓ create_checklist: creates with permissions ok")
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
        print("✓ save_answer: required bool with explicit True/False")
        it = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=1, question="Does it work?", answer_type="bool", required=True
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
        print("✓ save_answer: empty required text → required_value_missing")
        it = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=2, question="Describe", answer_type="text", required=True
        )
        ans, errs = svc.save_answer(
            technician_operating=self.tech_op, checklist=self.checklist, item_template=it, value="   "
        )
        self.assertIsNone(ans)
        self.assertIn("required_value_missing", errs)

    @patch("backend.apps.checklist.services.checklist_service.has_permission", return_value=(True, []))
    def test_save_answer_choice_not_in_options(self, _mock_perm):
        print("✓ save_answer: choice outside the options → choice_not_in_options")
        it = ChecklistItemTemplate.objects.create(
            template=self.tpl,
            order=3,
            question="Choose",
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
        print("✓ remove_answer: removes an existing one and handles a missing one")
        it = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=4, question="Remove?", answer_type="bool", required=False
        )
        # create an answer to remove
        a = ChecklistItemAnswer.objects.create(checklist=self.checklist, item_template=it, answer_bool=False)
        ok, errs = svc.remove_answer(
            technician_operating=self.tech_op, checklist=self.checklist, item_template=it
        )
        self.assertTrue(ok)
        self.assertEqual(errs, [])
        # try to remove again → not found
        ok2, errs2 = svc.remove_answer(
            technician_operating=self.tech_op, checklist=self.checklist, item_template=it
        )
        self.assertFalse(ok2)
        self.assertIn("item_answer_not_found", errs2)

    # -----------------------------
    # list_missing_required_answers
    # -----------------------------
    def test_list_missing_required_answers_basic(self):
        print("✓ list_missing_required_answers: identifies required items without an answer")
        it_bool = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=5, question="B?", answer_type="bool", required=True
        )
        it_text = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=6, question="T?", answer_type="text", required=True
        )
        it_opt = ChecklistItemTemplate.objects.create(
            template=self.tpl, order=7, question="Optional", answer_type="text", required=False
        )
        # answer only the bool
        ChecklistItemAnswer.objects.create(checklist=self.checklist, item_template=it_bool, answer_bool=False)

        missing, errs = svc.list_missing_required_answers(checklist=self.checklist)
        self.assertEqual(errs, [])
        # the text one (required) should be missing, and the optional one should not be listed
        self.assertIn(it_text.id, missing)
        self.assertNotIn(it_bool.id, missing)
        self.assertNotIn(it_opt.id, missing)

    # -----------------------------
    # bulk_save_answers
    # -----------------------------
    @patch("backend.apps.checklist.services.checklist_service.has_permission", return_value=(True, []))
    def test_bulk_save_answers_ok_not_found_and_error_bubbling(self, _mock_perm):
        print("✓ bulk_save_answers: saves several, accumulates errors, and ignores missing ones")

        # template items
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

        # checks
        self.assertTrue(any(isinstance(a, ChecklistItemAnswer) for a in saved))
        # should have errors for item_template_not_found and choice_not_in_options
        self.assertIn("item_template_not_found", errs)
        self.assertIn("choice_not_in_options", errs)
        # guarantee that the first one was saved
        self.assertTrue(ChecklistItemAnswer.objects.filter(checklist=self.checklist, item_template=it1).exists())
