# tests/test_checklist_validators.py
from django.test import TestCase
from backend.apps.checklist.validators.checklist_validator import (
    validate_checklist_template_payload,
    validate_checklist_item_template_payload,
    validate_checklist_item_answer_payload,
)


class ChecklistValidatorsTestCase(TestCase):
    def setUp(self):
        print("→ setUp: Preparando contexto para testes de validadores (sem DB)...")
        self.allowed_answer_types = {"bool", "text", "choice", "temperature", "height_cm", "number"}
        print("✓ allowed_answer_types definido:", self.allowed_answer_types)

    # -----------------------------
    # validate_checklist_template_payload
    # -----------------------------

    def test_template_payload_valid_minimal(self):
        print("✓ test_template_payload_valid_minimal: Payload básico válido")
        payload = {
            "name": "Instalação Padrão",
            "service_type": "Instalação",
            "is_active": True,
            "is_global": "0",
            "aggroupments": [1, 2, 3],
            "version": 1,
        }
        ok, errors = validate_checklist_template_payload(payload)
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_template_payload_invalid_name_length(self):
        print("✓ test_template_payload_invalid_name_length: Nome vazio deve falhar")
        payload = {"name": " ", "service_type": "X"}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_template_name_length", errors)

    def test_template_payload_invalid_name_chars(self):
        print("✓ test_template_payload_invalid_name_chars: Nome com ctrl char deve falhar")
        payload = {"name": "Nome\nQuebra", "service_type": "X"}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_template_name_chars", errors)

    def test_template_payload_invalid_service_type_length(self):
        print("✓ test_template_payload_invalid_service_type_length: service_type vazio deve falhar")
        payload = {"name": "Ok", "service_type": ""}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_service_type_length", errors)

    def test_template_payload_invalid_service_type_chars(self):
        print("✓ test_template_payload_invalid_service_type_chars: service_type com ctrl char deve falhar")
        payload = {"name": "Ok", "service_type": "Tipo\x00Invalido"}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_service_type_chars", errors)

    def test_template_payload_invalid_boolish_flags(self):
        print("✓ test_template_payload_invalid_boolish_flags: is_active/is_global não bool-ish devem falhar")
        payload = {"name": "Ok", "service_type": "X", "is_active": "yep", "is_global": None}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_is_active_type", errors)
        self.assertIn("invalid_is_global_type", errors)

    def test_template_payload_invalid_aggroupments_type(self):
        print("✓ test_template_payload_invalid_aggroupments_type: aggroupments não-lista deve falhar")
        payload = {"name": "Ok", "service_type": "X", "aggroupments": "1,2"}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_aggroupments_type", errors)

    def test_template_payload_invalid_aggroupment_id(self):
        print("✓ test_template_payload_invalid_aggroupment_id: id não positivo deve falhar")
        payload = {"name": "Ok", "service_type": "X", "aggroupments": [1, -2, 3]}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_aggroupment_id", errors)

    def test_template_payload_invalid_version_value(self):
        print("✓ test_template_payload_invalid_version_value: version inválido deve falhar")
        payload = {"name": "Ok", "service_type": "X", "version": -1}
        ok, errors = validate_checklist_template_payload(payload)
        self.assertFalse(ok)
        self.assertIn("invalid_version_value", errors)

    # -----------------------------
    # validate_checklist_item_template_payload
    # -----------------------------

    def test_item_template_payload_valid_bool(self):
        print("✓ test_item_template_payload_valid_bool: Payload válido com answer_type 'bool'")
        payload = {
            "order": 3,
            "question": "Está funcionando?",
            "answer_type": "bool",
            "required": "false",
        }
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_item_template_payload_valid_choice_with_options(self):
        print("✓ test_item_template_payload_valid_choice_with_options: 'choice' com opções válidas")
        payload = {
            "order": 1,
            "question": "Qual opção?",
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
        print("✓ test_item_template_payload_invalid_order_value: order não positivo deve falhar")
        payload = {"order": 0, "question": "Q", "answer_type": "bool"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_order_value", errors)

    def test_item_template_payload_invalid_question_length(self):
        print("✓ test_item_template_payload_invalid_question_length: question vazia deve falhar")
        payload = {"question": " ", "answer_type": "bool"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_question_length", errors)

    def test_item_template_payload_invalid_question_chars(self):
        print("✓ test_item_template_payload_invalid_question_chars: question com ctrl char deve falhar")
        payload = {"question": "Pergunta\x00Invalida", "answer_type": "bool"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_question_chars", errors)

    def test_item_template_payload_invalid_answer_type(self):
        print("✓ test_item_template_payload_invalid_answer_type: answer_type fora do allowed deve falhar")
        payload = {"question": "Ok", "answer_type": "unknown"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_answer_type", errors)

    def test_item_template_payload_invalid_required_type(self):
        print("✓ test_item_template_payload_invalid_required_type: required não bool-ish deve falhar")
        payload = {"question": "Ok", "answer_type": "bool", "required": "maybe"}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("invalid_required_type", errors)

    def test_item_template_payload_choice_empty_options(self):
        print("✓ test_item_template_payload_choice_empty_options: 'choice' sem opções deve falhar")
        payload = {"question": "Escolha", "answer_type": "choice", "choice_options": "   "}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("empty_choice_options", errors)

    def test_item_template_payload_choice_option_too_long(self):
        print("✓ test_item_template_payload_choice_option_too_long: opção >100 chars deve falhar")
        long_opt = "a" * 101
        payload = {"question": "Escolha", "answer_type": "choice", "choice_options": long_opt}
        ok, errors = validate_checklist_item_template_payload(
            payload, allowed_answer_types=self.allowed_answer_types
        )
        self.assertFalse(ok)
        self.assertIn("choice_option_too_long", errors)

    def test_item_template_payload_choice_option_invalid_chars(self):
        print("✓ test_item_template_payload_choice_option_invalid_chars: opção com ctrl char deve falhar")
        payload = {"question": "Escolha", "answer_type": "choice", "choice_options": "A\nB\x00C"}
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
        print("✓ test_answer_payload_bool_valid_variants: aceita True/'1'/'false'")
        for v in (True, "1", "false"):
            ok, errors = validate_checklist_item_answer_payload(answer_type="bool", value=v)
            self.assertTrue(ok, msg=f"Falhou para valor: {v}")
            self.assertEqual(errors, [])

    def test_answer_payload_bool_invalid(self):
        print("✓ test_answer_payload_bool_invalid: valor não bool-ish deve falhar")
        ok, errors = validate_checklist_item_answer_payload(answer_type="bool", value="maybe")
        self.assertFalse(ok)
        self.assertIn("invalid_bool_value", errors)

    # text
    def test_answer_payload_text_valid(self):
        print("✓ test_answer_payload_text_valid: texto simples válido")
        ok, errors = validate_checklist_item_answer_payload(answer_type="text", value="Descrição ok")
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_answer_payload_text_invalid_type(self):
        print("✓ test_answer_payload_text_invalid_type: valor não-string deve falhar")
        ok, errors = validate_checklist_item_answer_payload(answer_type="text", value=123)
        self.assertFalse(ok)
        self.assertIn("invalid_text_value", errors)

    def test_answer_payload_text_invalid_chars(self):
        print("✓ test_answer_payload_text_invalid_chars: texto com ctrl char deve falhar")
        ok, errors = validate_checklist_item_answer_payload(answer_type="text", value="Quebra\nLinha")
        self.assertFalse(ok)
        self.assertIn("invalid_text_chars", errors)

    # choice
    def test_answer_payload_choice_valid(self):
        print("✓ test_answer_payload_choice_valid: choice simples válido")
        ok, errors = validate_checklist_item_answer_payload(answer_type="choice", value="Opção A")
        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_answer_payload_choice_empty(self):
        print("✓ test_answer_payload_choice_empty: choice vazio deve falhar")
        ok, errors = validate_checklist_item_answer_payload(answer_type="choice", value="   ")
        self.assertFalse(ok)
        self.assertIn("invalid_choice_value", errors)

    def test_answer_payload_choice_too_long(self):
        print("✓ test_answer_payload_choice_too_long: choice >100 chars deve falhar")
        val = "x" * 101
        ok, errors = validate_checklist_item_answer_payload(answer_type="choice", value=val)
        self.assertFalse(ok)
        self.assertIn("choice_value_too_long", errors)

    def test_answer_payload_choice_invalid_chars(self):
        print("✓ test_answer_payload_choice_invalid_chars: choice com ctrl char deve falhar")
        ok, errors = validate_checklist_item_answer_payload(answer_type="choice", value="Inválido\x00")
        self.assertFalse(ok)
        self.assertIn("invalid_choice_chars", errors)

    # number-like (temperatures, heights, genérico)
    def test_answer_payload_number_valid_int_float_and_string(self):
        print("✓ test_answer_payload_number_valid_int_float_and_string: aceita 10, 3.14 e ' 2.5 '")
        for v in (10, 3.14, " 2.5 "):
            ok, errors = validate_checklist_item_answer_payload(answer_type="temperature", value=v)
            self.assertTrue(ok, msg=f"Falhou para valor: {v}")
            self.assertEqual(errors, [])

    def test_answer_payload_number_invalid(self):
        print("✓ test_answer_payload_number_invalid: valor não numérico deve falhar")
        for v in ("abc", None, {}, []):
            ok, errors = validate_checklist_item_answer_payload(answer_type="height_cm", value=v)
            self.assertFalse(ok, msg=f"Deveria falhar para: {v}")
            self.assertIn("invalid_number_value", errors)

    # note
    def test_answer_payload_note_invalid_chars(self):
        print("✓ test_answer_payload_note_invalid_chars: nota com ctrl char deve falhar")
        ok, errors = validate_checklist_item_answer_payload(
            answer_type="text", value="Ok", note="Observação\x00"
        )
        self.assertFalse(ok)
        self.assertIn("invalid_note_chars", errors)

    def test_answer_payload_note_valid(self):
        print("✓ test_answer_payload_note_valid: nota opcional válida")
        ok, errors = validate_checklist_item_answer_payload(
            answer_type="text", value="Ok", note="Observação normal"
        )
        self.assertTrue(ok)
        self.assertEqual(errors, [])
