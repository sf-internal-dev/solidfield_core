from django.test import TestCase
from backend.apps.checklist.utils import checklist_util


class ExpectedFieldAndHasRequiredValueTestCase(TestCase):
    def setUp(self):
        print("→ setUp: Testing expected_field_for_type and has_required_value")

    # -----------------------------
    # expected_field_for_type
    # -----------------------------
    def test_expected_field_for_known_types(self):
        print("✓ basic mapping bool/text/choice/number")
        self.assertEqual(checklist_util.expected_field_for_type("bool"), "answer_bool")
        self.assertEqual(checklist_util.expected_field_for_type("text"), "answer_texto")
        self.assertEqual(checklist_util.expected_field_for_type("choice"), "answer_choice")
        self.assertEqual(checklist_util.expected_field_for_type("temperature"), "answer_number")
        self.assertEqual(checklist_util.expected_field_for_type("number"), "answer_number")

    def test_expected_field_for_unknown_type(self):
        print("✓ unknown type returns None")
        self.assertIsNone(checklist_util.expected_field_for_type("weird_type"))

    # -----------------------------
    # has_required_value
    # -----------------------------
    def test_bypass_when_not_required(self):
        print("✓ required=False always returns True")
        for t in ["bool", "text", "choice", "number", "unknown"]:
            self.assertTrue(checklist_util.has_required_value(t, False, {}))

    def test_bool_required(self):
        print("✓ bool needs an explicit True/False")
        self.assertTrue(checklist_util.has_required_value("bool", True, {"answer_bool": True}))
        self.assertTrue(checklist_util.has_required_value("bool", True, {"answer_bool": False}))
        self.assertFalse(checklist_util.has_required_value("bool", True, {"answer_bool": None}))
        self.assertFalse(checklist_util.has_required_value("bool", True, {}))

    def test_text_required(self):
        print("✓ text requires a non-empty string")
        self.assertTrue(checklist_util.has_required_value("text", True, {"answer_texto": "ok"}))
        self.assertFalse(checklist_util.has_required_value("text", True, {"answer_texto": ""}))
        self.assertFalse(checklist_util.has_required_value("text", True, {"answer_texto": "   "}))
        self.assertFalse(checklist_util.has_required_value("text", True, {}))

    def test_choice_required(self):
        print("✓ choice requires a non-empty string")
        self.assertTrue(checklist_util.has_required_value("choice", True, {"answer_choice": "A"}))
        self.assertFalse(checklist_util.has_required_value("choice", True, {"answer_choice": ""}))
        self.assertFalse(checklist_util.has_required_value("choice", True, {"answer_choice": "  "}))
        self.assertFalse(checklist_util.has_required_value("choice", True, {}))

    def test_number_required(self):
        print("✓ number accepts int, float, and a non-empty string")
        # numeric directly
        self.assertTrue(checklist_util.has_required_value("number", True, {"answer_number": 10}))
        self.assertTrue(checklist_util.has_required_value("number", True, {"answer_number": 3.14}))
        # filled string (e.g. "5'9", "75%")
        self.assertTrue(checklist_util.has_required_value("number", True, {"answer_number": " 2.5 "}))
        self.assertTrue(checklist_util.has_required_value("height_in", True, {"answer_number": "5'9"}))
        # empty string
        self.assertFalse(checklist_util.has_required_value("number", True, {"answer_number": ""}))
        self.assertFalse(checklist_util.has_required_value("number", True, {"answer_number": "   "}))
        # missing
        self.assertFalse(checklist_util.has_required_value("number", True, {}))

    def test_unknown_type_required(self):
        print("✓ unknown type with required=True returns False")
        self.assertFalse(checklist_util.has_required_value("unknown", True, {"answer_texto": "some value"}))
