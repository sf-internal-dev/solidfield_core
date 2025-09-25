# backend/apps/clients/tests/test_address_utils.py

from django.test import SimpleTestCase

from backend.apps.clients.utils.client.client_address_util import validate_postal_code, validate_region_code, validate_coordinates


class ValidatePostalCodeTest(SimpleTestCase):
    # --- US ---
    def test_us_zip_valid_5_or_9(self):
        print("→ US ZIP: aceita 12345 e 12345-6789")
        self.assertTrue(validate_postal_code("12345", "US"))
        self.assertTrue(validate_postal_code("12345-6789", "US"))

    def test_us_zip_invalid_formats(self):
        print("→ US ZIP: rejeita formatos inválidos")
        self.assertFalse(validate_postal_code("1234", "US"))
        self.assertFalse(validate_postal_code("123456", "US"))
        self.assertFalse(validate_postal_code("1234A", "US"))
        self.assertFalse(validate_postal_code("12345-678", "US"))
        self.assertFalse(validate_postal_code("", "US"))
        self.assertFalse(validate_postal_code(None, "US"))

    # --- CA ---
    def test_ca_postal_valid_with_and_without_space(self):
        print("→ CA postal: aceita A1A 1A1 e A1A1A1")
        self.assertTrue(validate_postal_code("K1A 0B1", "CA"))  # Ottawa (exemplo clássico)
        self.assertTrue(validate_postal_code("K1A0B1", "CA"))

    def test_ca_postal_invalid(self):
        print("→ CA postal: rejeita letras proibidas/formatos errados")
        self.assertFalse(validate_postal_code("D1D 1D1", "CA"))  # D não permitido na 1ª posição
        self.assertFalse(validate_postal_code("K1A-0B1", "CA"))  # hífen não permitido
        self.assertFalse(validate_postal_code("K1A0B", "CA"))    # curto
        self.assertFalse(validate_postal_code("", "CA"))
        self.assertFalse(validate_postal_code(None, "CA"))

    # --- UK ---
    def test_uk_postcode_valid_common_and_gir(self):
        print("→ UK postcode: aceita padrões comuns e 'GIR 0AA'")
        self.assertTrue(validate_postal_code("SW1A 1AA", "UK"))  # Buckingham Palace
        self.assertTrue(validate_postal_code("EC1A 1BB", "UK"))
        self.assertTrue(validate_postal_code("GIR 0AA", "UK"))   # caso especial

    def test_uk_postcode_invalid(self):
        print("→ UK postcode: rejeita inválidos")
        self.assertFalse(validate_postal_code("SW1A1A", "UK"))    # curto
        self.assertFalse(validate_postal_code("SW1A-1AA", "UK"))  # hífen não permitido
        self.assertFalse(validate_postal_code("123 4AA", "UK"))   # começa com dígito inválido
        self.assertFalse(validate_postal_code("", "UK"))
        self.assertFalse(validate_postal_code(None, "UK"))

    # --- IE ---
    def test_ie_eircode_valid_with_and_without_space(self):
        print("→ IE Eircode: aceita 'A65 F4E2' e 'A65F4E2'")
        self.assertTrue(validate_postal_code("A65 F4E2", "IE"))
        self.assertTrue(validate_postal_code("A65F4E2", "IE"))

    def test_ie_eircode_invalid(self):
        print("→ IE Eircode: rejeita inválidos")
        self.assertFalse(validate_postal_code("A6 F4E2", "IE"))     # curto no routing key
        self.assertFalse(validate_postal_code("A65- F4E2", "IE"))   # hífen
        self.assertFalse(validate_postal_code("Z65 F4E2", "IE"))    # Z não permitido como 1º
        self.assertFalse(validate_postal_code("", "IE"))
        self.assertFalse(validate_postal_code(None, "IE"))

    # --- Unknown country ---
    def test_unknown_country_always_false(self):
        print("→ postal: país desconhecido → False")
        self.assertFalse(validate_postal_code("12345", "BR"))
        self.assertFalse(validate_postal_code("01001-000", "BR"))


class ValidateRegionCodeTest(SimpleTestCase):
    # Para US/CA, dependemos que US_STATES/CA_PROVINCES contenham estas chaves comuns
    def test_us_state_valid_and_invalid(self):
        print("→ US state: aceita siglas conhecidas, rejeita inválidas")
        self.assertTrue(validate_region_code("CA", "US"))  # California
        self.assertTrue(validate_region_code("NY", "US"))  # New York
        self.assertFalse(validate_region_code("XX", "US"))
        self.assertFalse(validate_region_code("", "US"))
        self.assertFalse(validate_region_code(None, "US"))

    def test_ca_province_valid_and_invalid(self):
        print("→ CA province: aceita siglas conhecidas, rejeita inválidas")
        self.assertTrue(validate_region_code("ON", "CA"))  # Ontario
        self.assertTrue(validate_region_code("QC", "CA"))  # Quebec
        self.assertFalse(validate_region_code("ZZ", "CA"))
        self.assertFalse(validate_region_code("", "CA"))
        self.assertFalse(validate_region_code(None, "CA"))

    def test_uk_ie_region_regex(self):
        print("→ UK/IE region: validação básica por regex (2–40 chars, letras/ espaço/ hífen)")
        self.assertTrue(validate_region_code("Greater London", "UK"))
        self.assertTrue(validate_region_code("County-Dublin", "IE"))
        self.assertFalse(validate_region_code("x", "UK"))                 # muito curto
        self.assertFalse(validate_region_code("this*is$invalid", "IE"))   # caracteres inválidos
        self.assertFalse(validate_region_code("", "UK"))
        self.assertFalse(validate_region_code(None, "IE"))

    def test_unknown_country_region_false(self):
        print("→ region: país desconhecido → False")
        self.assertFalse(validate_region_code("SP", "BR"))


class ValidateCoordinatesTest(SimpleTestCase):
    def test_coordinates_optional_none_is_true(self):
        print("→ coords: None/None é permitido (opcional)")
        self.assertTrue(validate_coordinates(None, None))
        self.assertTrue(validate_coordinates(None, 10.0))
        self.assertTrue(validate_coordinates(10.0, None))

    def test_coordinates_within_bounds(self):
        print("→ coords: limites inclusivos são válidos")
        self.assertTrue(validate_coordinates(0, 0))
        self.assertTrue(validate_coordinates(90, 180))
        self.assertTrue(validate_coordinates(-90, -180))
        self.assertTrue(validate_coordinates(45.123, -73.567))

    def test_coordinates_out_of_bounds(self):
        print("→ coords: fora dos limites são inválidos")
        self.assertFalse(validate_coordinates(91, 0))
        self.assertFalse(validate_coordinates(-91, 0))
        self.assertFalse(validate_coordinates(0, 181))
        self.assertFalse(validate_coordinates(0, -181))

    def test_coordinates_castable_to_float(self):
        print("→ coords: aceita strings numéricas")
        self.assertTrue(validate_coordinates("12.5", "-99.3"))
        print("→ coords: rejeita valores não numéricos")
        with self.assertRaises(ValueError):
            # sua função faz float(lat) e float(lng); se passar 'abc', vai estourar ValueError
            validate_coordinates("abc", "10")
