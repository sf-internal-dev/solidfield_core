import re
from unittest.mock import patch
from django.test import TestCase
from backend.apps.core.models import CompanyTenant
from backend.apps.core.utils.tenant.tenant_identifier_code_util import generate_tenant_identifier_code

class GenerateTenantIdentifierCodeTests(TestCase):
    def setUp(self):
        print("→ setUp: Preparando ambiente para testes de geração de tenant_code...")

    def test_generates_code_without_conflict(self):
        print("✓ test_generates_code_without_conflict: Geração de código simples sem conflito.")
        code = generate_tenant_identifier_code("solidfield")
        self.assertEqual(code, "SOLI")
        self.assertFalse(CompanyTenant.objects.filter(tenant_code=code).exists())

    def test_adds_suffix_if_conflict_exists(self):
        print("✓ test_adds_suffix_if_conflict_exists: Adição de sufixo em caso de conflito.")
        CompanyTenant.objects.create(tenant_code="SOLI", slug="solidfield")
        code = generate_tenant_identifier_code("solidfield")
        self.assertEqual(code, "SOLI1")

    def test_increments_suffix_until_available(self):
        print("✓ test_increments_suffix_until_available: Incrementa sufixos até tenant_code estar disponível.")
        for i in range(4):
            suffix = "" if i == 0 else str(i)
            CompanyTenant.objects.create(tenant_code=f"SOLI{suffix}",slug=f"solid-{i}")

        code = generate_tenant_identifier_code("solidfield")
        self.assertEqual(code, "SOLI4")

    def test_handles_special_characters_in_slug(self):
        print("✓ test_handles_special_characters_in_slug: Lida com caractéres especiais.")
        code = generate_tenant_identifier_code("sóli-d.f!eld")
        self.assertEqual(code, "SOLI")

    def test_short_slug_is_preserved(self):
        print("✓ test_short_slug_is_preserved: Verifica a preservação de slugs curtas.")
        code = generate_tenant_identifier_code("ab")
        self.assertEqual(code, "AB")

    def test_empty_slug_falls_back_to_COMP(self):
        print("✓ test_empty_slug_falls_back_to_COMP: Verifica se slug vazia tem fallback <COMP>.")
        code = generate_tenant_identifier_code("")
        self.assertTrue(code.startswith("COMP"))
        self.assertTrue(len(code) >= 4)

    def test_fallback_when_max_tries_reached(self):
        print("✓ test_fallback_when_max_tries_reached: Verifica fallback quando atinge máximo de tentativas.")
        for i in range(30):
            suffix = "" if i == 0 else str(i)
            CompanyTenant.objects.create(tenant_code=f"TEST{suffix}",slug=f"test-{i}")

        with patch("backend.apps.core.utils.tenant.tenant_identifier_code_util.get_random_string", return_value="ab"):
            code = generate_tenant_identifier_code("test")
            self.assertEqual(code, "TESTAB")

    def test_slug_with_accents_and_cedilla(self):
        print("✓ test_slug_with_accents_and_cedilla: Normalização de slug com cedilha e acentos.")
        # "çódê-company!" → normaliza para "codecompany" → "CODE"
        code = generate_tenant_identifier_code("çódê-company!")
        self.assertEqual(code, "CODE")

    def test_slug_with_multiple_accents(self):
        print("✓ test_slug_with_multiple_accents: Normalização de slug com vários acentos.")
        # "ação incrível" → "acao incrivel" → "ACAO"
        code = generate_tenant_identifier_code("ação incrível")
        self.assertEqual(code, "ACAO")

    def test_slug_with_circunflex_and_tilde(self):
        print("✓ test_slug_with_circunflex_and_tilde: Normalização de slug com circunflexo e til/tilde.")

        # "tênis-manhã" → "tenismanha" → "TENI"
        code = generate_tenant_identifier_code("tênis-manhã")
        self.assertEqual(code, "TENI")

    def test_slug_with_only_special_chars_and_accents(self):
        print("✓ test_slug_with_only_special_chars_and_accents: Normalização de slug apenas com caracteres especiais e acentos.")
        # "!çãõêé" → "caoee" → "CAOE"
        code = generate_tenant_identifier_code("!çãõêé")
        self.assertEqual(code, "CAOE")

    def test_slug_that_generates_comp_due_to_no_valid_chars(self):
        print("✓ test_slug_with_only_special_chars_and_accents: Fallback para COMP após erros com caracteres invalidos.")
        # All symbols → fallback default "COMP"
        code = generate_tenant_identifier_code("!!!$$$@@@")
        self.assertTrue(code.startswith("COMP"))
