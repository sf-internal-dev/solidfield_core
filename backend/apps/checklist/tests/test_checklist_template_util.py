from django.test import TestCase
from backend.apps.checklist.utils import checklist_template_util
from backend.apps.checklist.models import ChecklistTemplate, ChecklistItemTemplate
from backend.apps.core.models import CompanyTenant, Technician


class UtilsFunctionsTestCase(TestCase):
    def setUp(self):
        print("→ setUp: Creating tenant + technician + base template")
        self.tenant = CompanyTenant.objects.create(name="TenantTest", slug="tenant-test")
        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="techuser",
            social_name="Tech User",
            technician_permission="L1"
        )
        self.template = ChecklistTemplate.objects.create(
            tenant=self.tenant,
            name="Test Template",
            version=1,
            created_by=self.tech,
            service_type="Installation"
        )

    # -----------------------------
    # parse_choice_options
    # -----------------------------
    def test_parse_choice_options_splits_and_deduplicates(self):
        print("✓ parse_choice_options: splits commas/lines, strips spaces, deduplicates")
        raw = " A, B ,C\nA\n\nD "
        opts = checklist_template_util.parse_choice_options(raw)
        self.assertEqual(opts, ["A", "B", "C", "D"])

    def test_parse_choice_options_empty(self):
        print("✓ parse_choice_options: empty string → empty list")
        self.assertEqual(checklist_template_util.parse_choice_options(""), [])
        self.assertEqual(checklist_template_util.parse_choice_options(None), [])

    # -----------------------------
    # is_numeric_type / unit_for_type
    # -----------------------------
    def test_is_numeric_type_and_unit_for_type(self):
        print("✓ is_numeric_type / unit_for_type: recognizes numeric types")
        self.assertTrue(checklist_template_util.is_numeric_type("temperature"))
        self.assertEqual(checklist_template_util.unit_for_type("temperature"), "°C")
        self.assertFalse(checklist_template_util.is_numeric_type("text"))
        self.assertIsNone(checklist_template_util.unit_for_type("text"))

    # -----------------------------
    # parse_number_for_type / format_number_for_type
    # -----------------------------
    def test_parse_and_format_number_basic(self):
        print("✓ parse_number_for_type / format_number_for_type: basic values")
        v = checklist_template_util.parse_number_for_type("number", "2.5")
        self.assertEqual(v, 2.5)
        txt = checklist_template_util.format_number_for_type("number", v)
        self.assertIn("2.5", txt)

    def test_parse_and_format_temperature_f(self):
        print("✓ parse_number_for_type / format_number_for_type: Fahrenheit → °C")
        v = checklist_template_util.parse_number_for_type("temperature_f", 77)  # should yield 25 °C
        self.assertAlmostEqual(v, 25.0, places=1)
        txt = checklist_template_util.format_number_for_type("temperature_f", v)
        self.assertIn("°C", txt)

    def test_parse_and_format_height_in(self):
        print("✓ parse_number_for_type / format_number_for_type: imperial height")
        v = checklist_template_util.parse_number_for_type("height_in", "5'9")
        self.assertAlmostEqual(v, 175.26, places=2)
        txt = checklist_template_util.format_number_for_type("height_in", v)
        self.assertIn("m", txt)

    def test_parse_invalid_type_raises(self):
        print("✓ parse_number_for_type: invalid type raises ValueError")
        with self.assertRaises(ValueError):
            checklist_template_util.parse_number_for_type("notype", "123")

    # -----------------------------
    # has_unique_order_within_template
    # -----------------------------
    def test_has_unique_order_within_template_new_item(self):
        print("✓ has_unique_order_within_template: a new item with a free order should be True")
        item = ChecklistItemTemplate(template=self.template, order=1, question="Q1", answer_type="text")
        ok, errs = checklist_template_util.has_unique_order_within_template(item)
        self.assertTrue(ok)
        self.assertEqual(errs, [])

    def test_has_unique_order_within_template_conflict(self):
        print("✓ has_unique_order_within_template: an order conflict should fail")
        ChecklistItemTemplate.objects.create(template=self.template, order=1, question="Q1", answer_type="text")
        item = ChecklistItemTemplate(template=self.template, order=1, question="Q2", answer_type="text")
        ok, errs = checklist_template_util.has_unique_order_within_template(item)
        self.assertFalse(ok)
        self.assertIn("already exists", errs[0])

    # -----------------------------
    # next_order_for_template
    # -----------------------------
    def test_next_order_for_template_empty(self):
        print("✓ next_order_for_template: an empty template starts at 1")
        self.assertEqual(checklist_template_util.next_order_for_template(self.template), 1)

    def test_next_order_for_template_after_existing(self):
        print("✓ next_order_for_template: returns max+1")
        ChecklistItemTemplate.objects.create(template=self.template, order=1, question="Q1", answer_type="text")
        ChecklistItemTemplate.objects.create(template=self.template, order=2, question="Q2", answer_type="text")
        nxt = checklist_template_util.next_order_for_template(self.template)
        self.assertEqual(nxt, 3)
