import re
from unittest.mock import patch
from django.test import TestCase
from backend.apps.core.models import CompanyTenant
from backend.apps.core.utils.tenant.tenant_identifier_code_util import generate_tenant_code_attempts

class GenerateTenantIdentifierCodeTests(TestCase):
    def setUp(self):
        print("→ setUp: Preparing the environment for tenant_code generation tests...")

    def test_generates_code_without_conflict(self):
        print("✓ test_generates_code_without_conflict: Simple code generation with no conflict.")
        code = generate_tenant_code_attempts("solidfield")
        self.assertEqual(code, "SOLI")
        self.assertFalse(CompanyTenant.objects.filter(tenant_code=code).exists())

    def test_adds_suffix_if_conflict_exists(self):
        print("✓ test_adds_suffix_if_conflict_exists: Adds a suffix when there is a conflict.")
        CompanyTenant.objects.create(tenant_code="SOLI", slug="solidfield")
        code = generate_tenant_code_attempts("solidfield")
        self.assertEqual(code, "SOLI1")

    def test_increments_suffix_until_available(self):
        print("✓ test_increments_suffix_until_available: Increments suffixes until tenant_code is available.")
        for i in range(4):
            suffix = "" if i == 0 else str(i)
            CompanyTenant.objects.create(tenant_code=f"SOLI{suffix}",slug=f"solid-{i}")

        code = generate_tenant_code_attempts("solidfield")
        self.assertEqual(code, "SOLI4")

    def test_handles_special_characters_in_slug(self):
        print("✓ test_handles_special_characters_in_slug: Handles special characters.")
        code = generate_tenant_code_attempts("sóli-d.f!eld")
        self.assertEqual(code, "SOLI")

    def test_short_slug_is_preserved(self):
        print("✓ test_short_slug_is_preserved: Checks that short slugs are preserved.")
        code = generate_tenant_code_attempts("ab")
        self.assertEqual(code, "AB")

    def test_empty_slug_falls_back_to_COMP(self):
        print("✓ test_empty_slug_falls_back_to_COMP: Checks that an empty slug falls back to <COMP>.")
        code = generate_tenant_code_attempts("")
        self.assertTrue(code.startswith("COMP"))
        self.assertTrue(len(code) >= 4)

    def test_fallback_when_max_tries_reached(self):
        print("✓ test_fallback_when_max_tries_reached: Checks the fallback when the maximum number of attempts is reached.")
        for i in range(30):
            suffix = "" if i == 0 else str(i)
            CompanyTenant.objects.create(tenant_code=f"TEST{suffix}",slug=f"test-{i}")

        with patch("backend.apps.core.utils.tenant.tenant_identifier_code_util.get_random_string", return_value="ab"):
            code = generate_tenant_code_attempts("test")
            self.assertEqual(code, "TESTAB")

    def test_slug_with_accents_and_cedilla(self):
        print("✓ test_slug_with_accents_and_cedilla: Slug normalization with a cedilla and accents.")
        # "çódê-company!" → normalizes to "codecompany" → "CODE"
        code = generate_tenant_code_attempts("çódê-company!")
        self.assertEqual(code, "CODE")

    def test_slug_with_multiple_accents(self):
        print("✓ test_slug_with_multiple_accents: Slug normalization with several accents.")
        # "ação incrível" → "acao incrivel" → "ACAO"
        code = generate_tenant_code_attempts("ação incrível")
        self.assertEqual(code, "ACAO")

    def test_slug_with_circunflex_and_tilde(self):
        print("✓ test_slug_with_circunflex_and_tilde: Slug normalization with circumflex and tilde.")

        # "tênis-manhã" → "tenismanha" → "TENI"
        code = generate_tenant_code_attempts("tênis-manhã")
        self.assertEqual(code, "TENI")

    def test_slug_with_only_special_chars_and_accents(self):
        print("✓ test_slug_with_only_special_chars_and_accents: Slug normalization with only special characters and accents.")
        # "!çãõêé" → "caoee" → "CAOE"
        code = generate_tenant_code_attempts("!çãõêé")
        self.assertEqual(code, "CAOE")

    def test_slug_that_generates_comp_due_to_no_valid_chars(self):
        print("✓ test_slug_with_only_special_chars_and_accents: Falls back to COMP after errors with invalid characters.")
        # All symbols → fallback default "COMP"
        code = generate_tenant_code_attempts("!!!$$$@@@")
        self.assertTrue(code.startswith("COMP"))
