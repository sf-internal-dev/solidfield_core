# backend/apps/clients/tests/test_contact_validators.py

from django.test import SimpleTestCase

from backend.apps.clients.utils.client.client_registration_util import ( 
    validate_document_id,
    validate_phone_number,
)


class ValidateDocumentIdTest(SimpleTestCase):
    # ===== US =====
    def test_us_document_valid_ssn_and_ein(self):
        print("→ US doc: aceita SSN (com/sem hífen) e EIN")
        self.assertTrue(validate_document_id("123-45-6789", "US"))  # SSN com hífen
        self.assertTrue(validate_document_id("123456789", "US"))    # SSN sem hífen
        self.assertTrue(validate_document_id("12-3456789", "US"))   # EIN

    def test_us_document_invalid(self):
        print("→ US doc: rejeita formatos inválidos")
        self.assertFalse(validate_document_id("123-45-678", "US"))
        self.assertFalse(validate_document_id("12345678", "US"))
        self.assertFalse(validate_document_id("12-345678", "US"))
        self.assertFalse(validate_document_id("", "US"))
        self.assertFalse(validate_document_id(None, "US"))

    # ===== CA =====
    def test_ca_document_valid_sin_and_bn(self):
        print("→ CA doc: aceita SIN (com/sem hífen) e BN com sufixo opcional")
        self.assertTrue(validate_document_id("123-45-6789", "CA"))  # SIN com hífen
        self.assertTrue(validate_document_id("123456789", "CA"))    # SIN sem hífen
        self.assertTrue(validate_document_id("123456789 AB1234", "CA"))  # BN com sufixo

    def test_ca_document_invalid(self):
        print("→ CA doc: rejeita inválidos")
        self.assertFalse(validate_document_id("12345678", "CA"))          # curto
        self.assertFalse(validate_document_id("123456789 AB123", "CA"))   # sufixo curto
        self.assertFalse(validate_document_id("ABC456789", "CA"))         # letras no início
        self.assertFalse(validate_document_id("", "CA"))
        self.assertFalse(validate_document_id(None, "CA"))

    # ===== UK =====
    def test_uk_document_valid_nino_and_crn(self):
        print("→ UK doc: aceita NINO (AA999999A), CRN 8 dígitos, CRN alfanumérico (AA999999)")
        self.assertTrue(validate_document_id("AB123456C", "UK"))  # NINO
        self.assertTrue(validate_document_id("12345678", "UK"))   # CRN all digits
        self.assertTrue(validate_document_id("SC123456", "UK"))   # CRN letters+digits

    def test_uk_document_invalid(self):
        print("→ UK doc: rejeita inválidos")
        self.assertFalse(validate_document_id("A123456C", "UK"))    # NINO: falta 2ª letra inicial
        self.assertFalse(validate_document_id("AB12345", "UK"))     # curto (nem NINO nem CRN)
        self.assertFalse(validate_document_id("AB1234567", "UK"))   # longo demais p/ CRN/NINO
        self.assertFalse(validate_document_id("SC12345", "UK"))     # CRN alfanumérico curto
        self.assertFalse(validate_document_id("", "UK"))
        self.assertFalse(validate_document_id(None, "UK"))

    # ===== IE =====
    def test_ie_document_valid_pps_and_company(self):
        print("→ IE doc: aceita PPS (9999999X, A9999999X, etc.) e company numbers (6–7 dígitos ou letra+6)")
        self.assertTrue(validate_document_id("1234567A", "IE"))   # PPS 7 dígitos + letra
        self.assertTrue(validate_document_id("A1234567B", "IE"))  # PPS com prefixo letra
        self.assertTrue(validate_document_id("123456", "IE"))     # company number 6 dígitos
        self.assertTrue(validate_document_id("1234567", "IE"))    # company number 7 dígitos
        self.assertTrue(validate_document_id("C123456", "IE"))    # company number letra+6

    def test_ie_document_invalid(self):
        print("→ IE doc: rejeita inválidos")
        self.assertFalse(validate_document_id("123456A", "IE"))     # PPS curto
        self.assertFalse(validate_document_id("AB23456", "IE"))     # padrões não previstos
        self.assertFalse(validate_document_id("12345", "IE"))       # company curto
        self.assertFalse(validate_document_id("", "IE"))
        self.assertFalse(validate_document_id(None, "IE"))

    # ===== Unknown =====
    def test_unknown_country_document_false(self):
        print("→ doc país desconhecido: False")
        self.assertFalse(validate_document_id("123456789", "BR"))


class ValidatePhoneNumberTest(SimpleTestCase):
    # ===== US / CA =====
    def test_us_ca_phone_valid_formats(self):
        print("→ phone US/CA: aceita +1XXXXXXXXXX, (XXX) XXX-XXXX, XXX-XXX-XXXX, XXXXXXXXXX")
        for c in ("US", "CA"):
            self.assertTrue(validate_phone_number("+11234567890", c))
            self.assertTrue(validate_phone_number("(123) 456-7890", c))
            self.assertTrue(validate_phone_number("123-456-7890", c))
            self.assertTrue(validate_phone_number("1234567890", c))

    def test_us_ca_phone_invalid(self):
        print("→ phone US/CA: rejeita inválidos")
        for c in ("US", "CA"):
            self.assertFalse(validate_phone_number("+1123456789", c))    # curto
            self.assertFalse(validate_phone_number("123-45-67890", c))   # padrão errado
            self.assertFalse(validate_phone_number("(123)456-789", c))   # curto
            self.assertFalse(validate_phone_number("", c))
            self.assertFalse(validate_phone_number(None, c))

    # ===== UK =====
    def test_uk_phone_valid(self):
        print("→ phone UK: aceita +44XXXXXXXXXX (10 dígitos) e 0XXXXXXXXXX (11 dígitos)")
        self.assertTrue(validate_phone_number("+441234567890", "UK"))
        self.assertTrue(validate_phone_number("07123456789", "UK"))

    def test_uk_phone_invalid(self):
        print("→ phone UK: rejeita inválidos")
        self.assertFalse(validate_phone_number("+44123456789", "UK"))   # curto
        self.assertFalse(validate_phone_number("0712345678", "UK"))     # curto
        self.assertFalse(validate_phone_number("71234567890", "UK"))    # não começa com 0
        self.assertFalse(validate_phone_number("", "UK"))
        self.assertFalse(validate_phone_number(None, "UK"))

    # ===== IE =====
    def test_ie_phone_valid(self):
        print("→ phone IE: aceita +353XXXXXXXXX (9 após o +353) e 0XXXXXXXXX (10 com zero)")
        self.assertTrue(validate_phone_number("+353123456789", "IE"))  # 9 após +353
        self.assertTrue(validate_phone_number("0123456789", "IE"))     # 10 com zero

    def test_ie_phone_invalid(self):
        print("→ phone IE: rejeita inválidos")
        self.assertFalse(validate_phone_number("+35312345678", "IE"))  # curto
        self.assertFalse(validate_phone_number("012345678", "IE"))     # curto
        self.assertFalse(validate_phone_number("", "IE"))
        self.assertFalse(validate_phone_number(None, "IE"))

    # ===== Unknown =====
    def test_unknown_country_phone_false(self):
        print("→ phone país desconhecido: False")
        self.assertFalse(validate_phone_number("+5511999999999", "BR"))
