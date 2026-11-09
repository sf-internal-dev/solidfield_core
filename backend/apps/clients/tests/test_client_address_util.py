# backend/apps/clients/tests/test_address_utils.py

from django.test import SimpleTestCase
from backend.apps.clients.utils.client.client_address_util import (
    validate_postal_code,
    validate_region_code,
    validate_coordinates,
)


class ValidatePostalCodeTest(SimpleTestCase):
    # --- US ---
    def test_us_zip_valid_5_and_9(self):
        print("→ postal US: accepts 12345 and 12345-6789")
        self.assertTrue(validate_postal_code("12345", "US"))
        self.assertTrue(validate_postal_code("12345-6789", "US"))

    def test_us_zip_invalid(self):
        print("→ postal US: rejects invalid formats")
        self.assertFalse(validate_postal_code("1234", "US"))
        self.assertFalse(validate_postal_code("123456", "US"))
        self.assertFalse(validate_postal_code("1234A", "US"))
        self.assertFalse(validate_postal_code("12345-678", "US"))
        self.assertFalse(validate_postal_code("", "US"))
        self.assertFalse(validate_postal_code(None, "US"))

    # --- CA ---
    def test_ca_postal_valid_with_and_without_space(self):
        print("→ postal CA: accepts K1A 0B1 and K1A0B1")
        self.assertTrue(validate_postal_code("K1A 0B1", "CA"))
        self.assertTrue(validate_postal_code("K1A0B1", "CA"))

    def test_ca_postal_invalid(self):
        print("→ postal CA: rejects invalid values")
        self.assertFalse(validate_postal_code("D1D 1D1", "CA"))  # letter forbidden in the 1st position
        self.assertFalse(validate_postal_code("K1A-0B1", "CA"))  # hyphen not allowed
        self.assertFalse(validate_postal_code("K1A0B", "CA"))    # short
        self.assertFalse(validate_postal_code("", "CA"))
        self.assertFalse(validate_postal_code(None, "CA"))

    # --- UK ---
    def test_uk_postcode_valid_common_and_gir(self):
        print("→ postal UK: accepts common patterns and 'GIR 0AA'")
        self.assertTrue(validate_postal_code("SW1A 1AA", "UK"))
        self.assertTrue(validate_postal_code("EC1A 1BB", "UK"))
        self.assertTrue(validate_postal_code("GIR 0AA", "UK"))

    def test_uk_postcode_invalid(self):
        print("→ postal UK: rejects invalid values")
        self.assertFalse(validate_postal_code("SW1A1A", "UK"))    # short
        self.assertFalse(validate_postal_code("SW1A-1AA", "UK"))  # hyphen not allowed
        self.assertFalse(validate_postal_code("123 4AA", "UK"))   # starts with a digit
        self.assertFalse(validate_postal_code("", "UK"))
        self.assertFalse(validate_postal_code(None, "UK"))

    # --- IE ---
    def test_ie_eircode_valid_with_and_without_space(self):
        print("→ postal IE: accepts 'A65 F4E2' and 'A65F4E2'")
        self.assertTrue(validate_postal_code("A65 F4E2", "IE"))
        self.assertTrue(validate_postal_code("A65F4E2", "IE"))

    def test_ie_eircode_invalid(self):
        print("→ postal IE: rejects invalid values")
        self.assertFalse(validate_postal_code("A6 F4E2", "IE"))     # short routing key
        self.assertFalse(validate_postal_code("A65- F4E2", "IE"))   # hyphen
        self.assertFalse(validate_postal_code("Z65 F4E2", "IE"))    # Z not allowed as the 1st character
        self.assertFalse(validate_postal_code("", "IE"))
        self.assertFalse(validate_postal_code(None, "IE"))

    # --- Unknown country ---
    def test_unknown_country_returns_false(self):
        print("→ postal unknown country: always False")
        self.assertFalse(validate_postal_code("12345", "BR"))
        self.assertFalse(validate_postal_code("01001-000", "BR"))


class ValidateRegionCodeTest(SimpleTestCase):
    def test_us_membership_uppercase(self):
        print("→ region US: membership (uppercase) in US_STATES")
        self.assertTrue(validate_region_code("CA", "US"))  # California
        self.assertTrue(validate_region_code("NY", "US"))  # New York

    def test_us_membership_lowercase_fails(self):
        print("→ region US: lowercase does not pass (exact membership)")
        self.assertFalse(validate_region_code("ca", "US"))
        self.assertFalse(validate_region_code("ny", "US"))

    def test_ca_membership_uppercase(self):
        print("→ region CA: membership (uppercase) in CA_PROVINCES")
        self.assertTrue(validate_region_code("ON", "CA"))  # Ontario
        self.assertTrue(validate_region_code("QC", "CA"))  # Quebec

    def test_ca_membership_lowercase_fails(self):
        print("→ region CA: lowercase does not pass (exact membership)")
        self.assertFalse(validate_region_code("on", "CA"))
        self.assertFalse(validate_region_code("qc", "CA"))

    def test_ie_membership_abbreviations(self):
        print("→ region IE: accepts abbreviations (e.g., D, G, CO, WD)")
        self.assertTrue(validate_region_code("D", "IE"))    # Dublin
        self.assertTrue(validate_region_code("G", "IE"))    # Galway
        self.assertTrue(validate_region_code("CO", "IE"))   # Cork
        self.assertTrue(validate_region_code("WD", "IE"))   # Waterford
        self.assertFalse(validate_region_code("zz", "IE"))  # lowercase/unknown

    def test_uk_membership_named_regions(self):
        print("→ region UK: accepts named regions (upper) in UK_REGIONS")
        self.assertTrue(validate_region_code("GREATER LONDON", "UK"))
        self.assertTrue(validate_region_code("WEST MIDLANDS", "UK"))
        self.assertFalse(validate_region_code("Greater London", "UK"))  # case-sensitive
        self.assertFalse(validate_region_code("WAKANDA", "UK"))

    def test_region_empty_or_none(self):
        print("→ region: empty/None → False")
        self.assertFalse(validate_region_code("", "US"))
        self.assertFalse(validate_region_code(None, "US"))

    def test_unknown_country_region_false(self):
        print("→ region unknown country: False")
        self.assertFalse(validate_region_code("SP", "BR"))
        self.assertFalse(validate_region_code("Any", "ZZ"))


class ValidateCoordinatesTest(SimpleTestCase):
    def test_optional_none_is_true(self):
        print("→ coords: None/None is allowed (optional)")
        self.assertTrue(validate_coordinates(None, None))
        self.assertTrue(validate_coordinates(None, 10.0))
        self.assertTrue(validate_coordinates(10.0, None))

    def test_within_bounds(self):
        print("→ coords: inclusive bounds are valid")
        self.assertTrue(validate_coordinates(0, 0))
        self.assertTrue(validate_coordinates(90, 180))
        self.assertTrue(validate_coordinates(-90, -180))
        self.assertTrue(validate_coordinates(45.123, -73.567))

    def test_out_of_bounds(self):
        print("→ coords: values outside the bounds are invalid")
        self.assertFalse(validate_coordinates(91, 0))
        self.assertFalse(validate_coordinates(-91, 0))
        self.assertFalse(validate_coordinates(0, 181))
        self.assertFalse(validate_coordinates(0, -181))

    def test_castable_to_float(self):
        print("→ coords: accepts numeric strings and rejects non-numeric ones (ValueError)")
        self.assertTrue(validate_coordinates("12.5", "-99.3"))
        with self.assertRaises(ValueError):
            validate_coordinates("abc", "10")
