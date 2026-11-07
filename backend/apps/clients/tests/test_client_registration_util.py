# backend/apps/clients/tests/test_contact_validators.py

from django.test import SimpleTestCase

from backend.apps.clients.utils.client.client_registration_util import ( 
    validate_document_id,
    validate_phone_number,
)


class ValidateDocumentIdTest(SimpleTestCase):
    # ===== US =====
    def test_us_document_valid_ssn_and_ein(self):
        print("→ US doc: accepts SSN (with/without hyphen) and EIN")
        self.assertTrue(validate_document_id("123-45-6789", "US"))  # SSN with hyphen
        self.assertTrue(validate_document_id("123456789", "US"))    # SSN without hyphen
        self.assertTrue(validate_document_id("12-3456789", "US"))   # EIN

    def test_us_document_invalid(self):
        print("→ US doc: rejects invalid formats")
        self.assertFalse(validate_document_id("123-45-678", "US"))
        self.assertFalse(validate_document_id("12345678", "US"))
        self.assertFalse(validate_document_id("12-345678", "US"))
        self.assertFalse(validate_document_id("", "US"))
        self.assertFalse(validate_document_id(None, "US"))

    # ===== CA =====
    def test_ca_document_valid_sin_and_bn(self):
        print("→ CA doc: accepts SIN (with/without hyphen) and BN with an optional suffix")
        self.assertTrue(validate_document_id("123-45-6789", "CA"))  # SIN with hyphen
        self.assertTrue(validate_document_id("123456789", "CA"))    # SIN without hyphen
        self.assertTrue(validate_document_id("123456789 AB1234", "CA"))  # BN with suffix

    def test_ca_document_invalid(self):
        print("→ CA doc: rejects invalid values")
        self.assertFalse(validate_document_id("12345678", "CA"))          # short
        self.assertFalse(validate_document_id("123456789 AB123", "CA"))   # short suffix
        self.assertFalse(validate_document_id("ABC456789", "CA"))         # letters at the start
        self.assertFalse(validate_document_id("", "CA"))
        self.assertFalse(validate_document_id(None, "CA"))

    # ===== UK =====
    def test_uk_document_valid_nino_and_crn(self):
        print("→ UK doc: accepts NINO (AA999999A), 8-digit CRN, alphanumeric CRN (AA999999)")
        self.assertTrue(validate_document_id("AB123456C", "UK"))  # NINO
        self.assertTrue(validate_document_id("12345678", "UK"))   # CRN all digits
        self.assertTrue(validate_document_id("SC123456", "UK"))   # CRN letters+digits

    def test_uk_document_invalid(self):
        print("→ UK doc: rejects invalid values")
        self.assertFalse(validate_document_id("A123456C", "UK"))    # NINO: missing the 2nd leading letter
        self.assertFalse(validate_document_id("AB12345", "UK"))     # short (neither NINO nor CRN)
        self.assertFalse(validate_document_id("AB1234567", "UK"))   # too long for CRN/NINO
        self.assertFalse(validate_document_id("SC12345", "UK"))     # short alphanumeric CRN
        self.assertFalse(validate_document_id("", "UK"))
        self.assertFalse(validate_document_id(None, "UK"))

    # ===== IE =====
    def test_ie_document_valid_pps_and_company(self):
        print("→ IE doc: accepts PPS (9999999X, A9999999X, etc.) and company numbers (6–7 digits or letter+6)")
        self.assertTrue(validate_document_id("1234567A", "IE"))   # PPS: 7 digits + letter
        self.assertTrue(validate_document_id("A1234567B", "IE"))  # PPS with a letter prefix
        self.assertTrue(validate_document_id("123456", "IE"))     # company number: 6 digits
        self.assertTrue(validate_document_id("1234567", "IE"))    # company number: 7 digits
        self.assertTrue(validate_document_id("C123456", "IE"))    # company number: letter+6

    def test_ie_document_invalid(self):
        print("→ IE doc: rejects invalid values")
        self.assertFalse(validate_document_id("123456A", "IE"))     # short PPS
        self.assertFalse(validate_document_id("AB23456", "IE"))     # patterns not covered
        self.assertFalse(validate_document_id("12345", "IE"))       # short company number
        self.assertFalse(validate_document_id("", "IE"))
        self.assertFalse(validate_document_id(None, "IE"))

    # ===== Unknown =====
    def test_unknown_country_document_false(self):
        print("→ doc unknown country: False")
        self.assertFalse(validate_document_id("123456789", "BR"))


class ValidatePhoneNumberTest(SimpleTestCase):
    # ===== US / CA =====
    def test_us_ca_phone_valid_formats(self):
        print("→ phone US/CA: accepts +1XXXXXXXXXX, (XXX) XXX-XXXX, XXX-XXX-XXXX, XXXXXXXXXX")
        for c in ("US", "CA"):
            self.assertTrue(validate_phone_number("+11234567890", c))
            self.assertTrue(validate_phone_number("(123) 456-7890", c))
            self.assertTrue(validate_phone_number("123-456-7890", c))
            self.assertTrue(validate_phone_number("1234567890", c))

    def test_us_ca_phone_invalid(self):
        print("→ phone US/CA: rejects invalid values")
        for c in ("US", "CA"):
            self.assertFalse(validate_phone_number("+1123456789", c))    # short
            self.assertFalse(validate_phone_number("123-45-67890", c))   # wrong pattern
            self.assertFalse(validate_phone_number("(123)456-789", c))   # short
            self.assertFalse(validate_phone_number("", c))
            self.assertFalse(validate_phone_number(None, c))

    # ===== UK =====
    def test_uk_phone_valid(self):
        print("→ phone UK: accepts +44XXXXXXXXXX (10 digits) and 0XXXXXXXXXX (11 digits)")
        self.assertTrue(validate_phone_number("+441234567890", "UK"))
        self.assertTrue(validate_phone_number("07123456789", "UK"))

    def test_uk_phone_invalid(self):
        print("→ phone UK: rejects invalid values")
        self.assertFalse(validate_phone_number("+44123456789", "UK"))   # short
        self.assertFalse(validate_phone_number("0712345678", "UK"))     # short
        self.assertFalse(validate_phone_number("71234567890", "UK"))    # does not start with 0
        self.assertFalse(validate_phone_number("", "UK"))
        self.assertFalse(validate_phone_number(None, "UK"))

    # ===== IE =====
    def test_ie_phone_valid(self):
        print("→ phone IE: accepts +353XXXXXXXXX (9 after +353) and 0XXXXXXXXX (10 with a leading zero)")
        self.assertTrue(validate_phone_number("+353123456789", "IE"))  # 9 after +353
        self.assertTrue(validate_phone_number("0123456789", "IE"))     # 10 with a leading zero

    def test_ie_phone_invalid(self):
        print("→ phone IE: rejects invalid values")
        self.assertFalse(validate_phone_number("+35312345678", "IE"))  # short
        self.assertFalse(validate_phone_number("012345678", "IE"))     # short
        self.assertFalse(validate_phone_number("", "IE"))
        self.assertFalse(validate_phone_number(None, "IE"))

    # ===== Unknown =====
    def test_unknown_country_phone_false(self):
        print("→ phone unknown country: False")
        self.assertFalse(validate_phone_number("+5511999999999", "BR"))
