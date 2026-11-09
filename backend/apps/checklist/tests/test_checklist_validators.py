# tests/test_checklist_validators.py
from django.test import TestCase
from backend.apps.checklist.validators.checklist_validator import (
    validate_checklist_template_payload,
    validate_checklist_item_template_payload,
    validate_checklist_item_answer_payload,
)


class ChecklistValidatorsTestCase(TestCase):
    def setUp(self):
        print("→ setUp: Preparing context for validator tests (no DB)...")
        self.allowed_answer_types = {"bool", "text", "choice", "temperature", "height_cm", "number"}
        print("✓ allowed_answer_types defined:", self.allowed_answer_types)

    # -----------------------------
    # validate_checklist_template_payload
    # -----------------------------

    def test_template_payload_valid_minimal(self):
        print("✓ test_template_payload_valid_minimal: Valid basic payload")
        payload = {
            "name": "Standard Installation",
            "service_type": "Installation",
            "is_active": True,
            "is_global": "0",
            "aggroupments": [1, 2, 3],
            "version": 1,
        }
        ok, errors = validate_checklist_template_payload(payload)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_template_payload_invalid_name_length(self):
        print("✓ test_template_payload_invalid_name_length: Empty name should fail")
        payload = {"name": " ", "service_type": "X"}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_template_name_length", errors)

    def test_template_payload_invalid_service_type_length(self):
        print("✓ test_template_payload_invalid_service_type_length: empty service_type should fail")
        payload = {"name": "Ok", "service_type": ""}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_service_type_length", errors)

    def test_template_payload_invalid_service_type_chars(self):
        print("✓ test_template_payload_invalid_service_type_chars: service_type with a ctrl char should fail")
        payload = {"name": "Ok", "service_type": "Type\x00Invalid"}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_service_type_chars", errors)

    def test_template_payload_invalid_boolish_flags(self):
        print("✓ test_template_payload_invalid_boolish_flags: is_active/is_global that are not bool-ish should fail")
        payload = {"name": "Ok", "service_type": "X", "is_active": "yep", "is_global": None}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_is_active_type", errors)
        self.assertIn("invalid_is_global_type", errors)

    def test_template_payload_invalid_aggroupments_type(self):
        print("✓ test_template_payload_invalid_aggroupments_type: aggroupments that are not a list should fail")
        payload = {"name": "Ok", "service_type": "X", "aggroupments": "1,2"}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_aggroupments_type", errors)

    def test_template_payload_invalid_aggroupment_id(self):
        print("✓ test_template_payload_invalid_aggroupment_id: a non-positive id should fail")
        payload = {"name": "Ok", "service_type": "X", "aggroupments": [1, -2, 3]}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_aggroupment_id", errors)

    def test_template_payload_invalid_version_value(self):
        print("✓ test_template_payload_invalid_version_value: an invalid version should fail")
        payload = {"name": "Ok", "service_type": "X", "version": -1}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_version_value", errors)

    # -----------------------------
    # validate_checklist_item_template_payload
    # -----------------------------

    def test_item_template_payload_valid_bool(self):
        print("✓ test_item_template_payload_valid_bool: Valid payload with answer_type 'bool'")
        payload = {
            "order": 3,
            "question": "Is it working?",
            "answer_type": "bool",
            "required": "false",
        }
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_item_template_payload_valid_choice_with_options(self):
        print("✓ test_item_template_payload_valid_choice_with_options: 'choice' with valid options")
        payload = {
            "order": 1,
            "question": "Which option?",
            "answer_type": "choice",
            "required": True,
            "choice_options": "A\nB\nC",
        }
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_item_template_payload_invalid_order_value(self):
        print("✓ test_item_template_payload_invalid_order_value: a non-positive order should fail")
        payload = {"order": 0, "question": "Q", "answer_type": "bool"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_order_value", errors)

    def test_item_template_payload_invalid_question_length(self):
        print("✓ test_item_template_payload_invalid_question_length: an empty question should fail")
        payload = {"question": " ", "answer_type": "bool"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_question_length", errors)

    def test_item_template_payload_invalid_question_chars(self):
        print("✓ test_item_template_payload_invalid_question_chars: a question with a ctrl char should fail")
        payload = {"question": "Question\x00Invalid", "answer_type": "bool"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_question_chars", errors)

    def test_item_template_payload_invalid_answer_type(self):
        print("✓ test_item_template_payload_invalid_answer_type: an answer_type outside allowed should fail")
        payload = {"question": "Ok", "answer_type": "unknown"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_answer_type", errors)

    def test_item_template_payload_invalid_required_type(self):
        print("✓ test_item_template_payload_invalid_required_type: required that is not bool-ish should fail")
        payload = {"question": "Ok", "answer_type": "bool", "required": "maybe"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_required_type", errors)

    def test_item_template_payload_choice_empty_options(self):
        print("✓ test_item_template_payload_choice_empty_options: 'choice' without options should fail")
        payload = {"question": "Choose", "answer_type": "choice", "choice_options": "   "}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("empty_choice_options", errors)

    def test_item_template_payload_choice_option_too_long(self):
        print("✓ test_item_template_payload_choice_option_too_long: an option >100 chars should fail")
        long_opt = "a" * 101
        payload = {"question": "Choose", "answer_type": "choice", "choice_options": long_opt}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("choice_option_too_long", errors)

    def test_item_template_payload_choice_option_invalid_chars(self):
        print("✓ test_item_template_payload_choice_option_invalid_chars: an option with a ctrl char should fail")
        payload = {"question": "Choose", "answer_type": "choice", "choice_options": "A\nB\x00C"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_choice_option_chars", errors)

    # -----------------------------
    # validate_checklist_item_answer_payload
    # -----------------------------

    # bool
    def test_answer_payload_bool_valid_variants(self):
        print("✓ test_answer_payload_bool_valid_variants: accepts True/'1'/'false'")
        for v in (True, "1", "false"):
            ok, errors = validate_checklist_item_answer_payload(answer_type="bool", value=v)
            self.assertTrue(ok, msg=f"Failed for value: {v}")
            self.assertEqual(errors, [])

    def test_answer_payload_bool_invalid(self):
        print("✓ test_answer_payload_bool_invalid: a value that is not bool-ish should fail")
        ok, errors = validate_checklist_item_answer_payload(answer_type="bool", value="maybe")
        self.assertFalse(ok)
        self.assertIn("invalid_bool_value", errors)

    # text
    def test_answer_payload_text_valid(self):
        print("✓ test_answer_payload_text_valid: valid plain text")
        ok, errors = validate_checklist_item_answer_payload(answer_type="text", value="Description ok")
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_answer_payload_text_invalid_type(self):
        print("✓ test_answer_payload_text_invalid_type: a non-string value should fail")
        ok, errors = validate_checklist_item_answer_payload(answer_type="text", value=123)
        self.assertFalse(ok)
        self.assertIn("invalid_text_value", errors)

    # choice
    def test_answer_payload_choice_valid(self):
        print("✓ test_answer_payload_choice_valid: valid simple choice")
        ok, errors = validate_checklist_item_answer_payload(answer_type="choice", value="Option A")
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_answer_payload_choice_empty(self):
        print("✓ test_answer_payload_choice_empty: an empty choice should fail")
        ok, errors = validate_checklist_item_answer_payload(answer_type="choice", value="   ")
        self.assertFalse(ok)
        self.assertIn("invalid_choice_value", errors)

    def test_answer_payload_choice_too_long(self):
        print("✓ test_answer_payload_choice_too_long: a choice >100 chars should fail")
        val = "x" * 101
        ok, errors = validate_checklist_item_answer_payload(answer_type="choice", value=val)
        self.assertFalse(ok)
        self.assertIn("choice_value_too_long", errors)

    def test_answer_payload_choice_invalid_chars(self):
        print("✓ test_answer_payload_choice_invalid_chars: a choice with a ctrl char should fail")
        ok, errors = validate_checklist_item_answer_payload(answer_type="choice", value="Invalid\x00")
        self.assertFalse(ok)
        self.assertIn("invalid_choice_chars", errors)

    # number-like (temperatures, heights, generic)
    def test_answer_payload_number_valid_int_float_and_string(self):
        print("✓ test_answer_payload_number_valid_int_float_and_string: accepts 10, 3.14, and ' 2.5 '")
        for v in (10, 3.14, " 2.5 "):
            ok, errors = validate_checklist_item_answer_payload(answer_type="temperature", value=v)
            self.assertTrue(ok, msg=f"Failed for value: {v}")
            self.assertEqual(errors, [])

    def test_answer_payload_number_invalid(self):
        print("✓ test_answer_payload_number_invalid: a non-numeric value should fail")
        for v in ("abc", None, {}, []):
            ok, errors = validate_checklist_item_answer_payload(answer_type="height_cm", value=v)
            self.assertFalse(ok, msg=f"Should fail for: {v}")
            self.assertIn("invalid_number_value", errors)

    # note
    def test_answer_payload_note_invalid_chars(self):
        print("✓ test_answer_payload_note_invalid_chars: a note with a ctrl char should fail")
        ok, errors = validate_checklist_item_answer_payload(
            answer_type="text", value="Ok", note="Note\x00"
        )
        self.assertFalse(ok)
        self.assertIn("invalid_note_chars", errors)

    def test_answer_payload_note_valid(self):
        print("✓ test_answer_payload_note_valid: valid optional note")
        ok, errors = validate_checklist_item_answer_payload(
            answer_type="text", value="Ok", note="Normal note"
        )
        self.assertTrue(ok)
        self.assertEqual(errors, [])
