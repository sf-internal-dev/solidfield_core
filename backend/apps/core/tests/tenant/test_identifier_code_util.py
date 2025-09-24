# backend/apps/core/tests/utils/test_generate_tenant_code_attempts.py

from django.test import SimpleTestCase

from backend.apps.core.utils.tenant.tenant_identifier_code_util import generate_tenant_code_attempts


class GenerateTenantCodeAttemptsTest(SimpleTestCase):
    def test_basic_slug_default_30(self):
        codes = generate_tenant_code_attempts("solid field")  # default 30
        self.assertEqual(len(codes), 30)
        # base deve ser "SOLI"
        self.assertEqual(codes[:5], ["SOLI", "SOLI1", "SOLI2", "SOLI3", "SOLI4"])
        # sem duplicatas
        self.assertEqual(len(codes), len(set(codes)))

    def test_non_ascii_accents_are_stripped(self):
        # "çãõ Áéî" → NFKD → "cao Aei" → A-Z/0-9 only → "CAOAEI" → [:4] = "CAOA"
        codes = generate_tenant_code_attempts("çãõ Áéî", max_tries=5)
        self.assertEqual(codes[:3], ["CAOA", "CAOA1", "CAOA2"])

    def test_symbols_are_removed_and_base_uppercased(self):
        # "A!@#B$%C^&*()D" → "ABCD"
        codes = generate_tenant_code_attempts("A!@#B$%C^&*()D", max_tries=5)
        self.assertEqual(codes, ["ABCD", "ABCD1", "ABCD2", "ABCD3", "ABCD4"])

    def test_empty_slug_falls_back_to_COMP(self):
        codes = generate_tenant_code_attempts("", max_tries=4)
        self.assertEqual(codes, ["COMP", "COMP1", "COMP2", "COMP3"])

    def test_short_slug_keeps_short_base(self):
        # "123" → base "123" (menos de 4) continua válido
        codes = generate_tenant_code_attempts("123", max_tries=4)
        self.assertEqual(codes, ["123", "1231", "1232", "1233"])

    def test_max_tries_respected_and_increments(self):
        codes = generate_tenant_code_attempts("beta corp", max_tries=3)
        self.assertEqual(len(codes), 3)
        self.assertEqual(codes, ["BETA", "BETA1", "BETA2"])

    def test_uniqueness_and_order(self):
        codes = generate_tenant_code_attempts("solid field", max_tries=10)
        # ordem incremental exata
        expected = ["SOLI"] + [f"SOLI{i}" for i in range(1, 10)]
        self.assertEqual(codes, expected)
        # todos únicos
        self.assertEqual(len(codes), len(set(codes)))
