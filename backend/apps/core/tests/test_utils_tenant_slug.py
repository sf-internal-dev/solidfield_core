from django.test import TestCase
from backend.apps.core.utils.tenant.tenant_slug_util import sanitize_tenant_slug, suggest_company_slug  # ajuste o caminho conforme sua estrutura

class SanitizeTenantSlugTests(TestCase):
    def test_basic_slug(self):
        print("✓ test_basic_slug: converte para minúsculo e remove símbolos")
        self.assertEqual(sanitize_tenant_slug("BlueCompany"), "bluecompany")

    def test_with_accents_and_uppercase(self):
        print("✓ test_with_accents_and_uppercase: remove acentos e deixa minúsculo")
        self.assertEqual(sanitize_tenant_slug("JoãoÁÉÇ"), "joaoaec")

    def test_with_numbers_and_symbols(self):
        print("✓ test_with_numbers_and_symbols: mantém números, remove símbolos")
        self.assertEqual(sanitize_tenant_slug("My@123#Company!"), "my123company")

    def test_with_only_symbols(self):
        print("✓ test_with_only_symbols: retorna string vazia")
        self.assertEqual(sanitize_tenant_slug("!@#$%^&*()"), "")

    def test_non_latin_characters(self):
        print("✓ test_non_latin_characters: remove caracteres não-romanos")
        self.assertEqual(sanitize_tenant_slug("株式会社テスト"), "")

    def test_empty_input(self):
        print("✓ test_empty_input: retorna string vazia para input vazio")
        self.assertEqual(sanitize_tenant_slug(""), "")


class SuggestCompanySlugTests(TestCase):
    def test_single_clean_word(self):
        print("✓ test_single_clean_word: retorna o nome único limpo")
        self.assertEqual(suggest_company_slug("BlueCompany"), ["bluecompany"])

    def test_two_words(self):
        print("✓ test_two_words: combinações com duas palavras")
        result = suggest_company_slug("Blue Tech")
        self.assertGreaterEqual(len(result), 1)
        self.assertTrue(all(isinstance(s, str) and s for s in result))
        self.assertTrue(all(s.islower() for s in result))

    def test_three_words(self):
        print("✓ test_three_words: gera 3 sugestões ou mais")
        result = suggest_company_slug("Blue Data Labs")
        self.assertGreaterEqual(len(result), 2)
        self.assertTrue("bluedata" in result or "bluedatalabs" in result)

    def test_with_accents_and_symbols(self):
        print("✓ test_with_accents_and_symbols: sanitiza corretamente")
        result = suggest_company_slug("João & Cia Tech!")
        self.assertTrue(any("joao" in s for s in result))
        self.assertTrue(all(s.islower() and s.isalnum() for s in result))

    def test_removes_duplicates(self):
        print("✓ test_removes_duplicates: evita sugestões repetidas")
        result = suggest_company_slug("Data Data Data")
        self.assertEqual(len(result), len(set(result)))
        self.assertGreaterEqual(len(result), 1)


    def test_empty_string(self):
        print("✓ test_empty_string: retorna lista vazia para nome vazio")
        self.assertEqual(suggest_company_slug(""), [])

    def test_symbols_only(self):
        print("✓ test_symbols_only: retorna lista vazia para entrada inválida")
        self.assertEqual(suggest_company_slug("@@@ !!! ???"), [])

    def test_non_latin_name(self):
        print("✓ test_non_latin_name: ignora nomes não latinos")
        self.assertEqual(suggest_company_slug("株式会社テスト"), [])

    def test_one_valid_word_others_invalid(self):
        print("✓ test_one_valid_word_others_invalid: considera apenas partes válidas")
        self.assertEqual(suggest_company_slug("Tech @@@"), ["tech"])
