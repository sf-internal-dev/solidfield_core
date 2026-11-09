from django.test import TestCase
from backend.apps.core.utils.tenant.tenant_slug_util import sanitize_tenant_slug, suggest_company_slug  # adjust the path to match your structure

class SanitizeTenantSlugTests(TestCase):
    def test_basic_slug(self):
        print("✓ test_basic_slug: converts to lowercase and removes symbols")
        self.assertEqual(sanitize_tenant_slug("BlueCompany"), "bluecompany")

    def test_with_accents_and_uppercase(self):
        print("✓ test_with_accents_and_uppercase: removes accents and lowercases")
        self.assertEqual(sanitize_tenant_slug("JoãoÁÉÇ"), "joaoaec")

    def test_with_numbers_and_symbols(self):
        print("✓ test_with_numbers_and_symbols: keeps numbers, removes symbols")
        self.assertEqual(sanitize_tenant_slug("My@123#Company!"), "my123company")

    def test_with_only_symbols(self):
        print("✓ test_with_only_symbols: returns an empty string")
        self.assertEqual(sanitize_tenant_slug("!@#$%^&*()"), "")

    def test_non_latin_characters(self):
        print("✓ test_non_latin_characters: removes non-Roman characters")
        self.assertEqual(sanitize_tenant_slug("株式会社テスト"), "")

    def test_empty_input(self):
        print("✓ test_empty_input: returns an empty string for empty input")
        self.assertEqual(sanitize_tenant_slug(""), "")


class SuggestCompanySlugTests(TestCase):
    def test_single_clean_word(self):
        print("✓ test_single_clean_word: returns the single cleaned name")
        self.assertEqual(suggest_company_slug("BlueCompany"), ["bluecompany"])

    def test_two_words(self):
        print("✓ test_two_words: combinations with two words")
        result = suggest_company_slug("Blue Tech")
        self.assertGreaterEqual(len(result), 1)
        self.assertTrue(all(isinstance(s, str) and s for s in result))
        self.assertTrue(all(s.islower() for s in result))

    def test_three_words(self):
        print("✓ test_three_words: generates 3 suggestions or more")
        result = suggest_company_slug("Blue Data Labs")
        self.assertGreaterEqual(len(result), 2)
        self.assertTrue("bluedata" in result or "bluedatalabs" in result)

    def test_with_accents_and_symbols(self):
        print("✓ test_with_accents_and_symbols: sanitizes correctly")
        result = suggest_company_slug("João & Co Tech!")
        self.assertTrue(any("joao" in s for s in result))
        self.assertTrue(all(s.islower() and s.isalnum() for s in result))

    def test_removes_duplicates(self):
        print("✓ test_removes_duplicates: avoids repeated suggestions")
        result = suggest_company_slug("Data Data Data")
        self.assertEqual(len(result), len(set(result)))
        self.assertGreaterEqual(len(result), 1)


    def test_empty_string(self):
        print("✓ test_empty_string: returns an empty list for an empty name")
        self.assertEqual(suggest_company_slug(""), [])

    def test_symbols_only(self):
        print("✓ test_symbols_only: returns an empty list for invalid input")
        self.assertEqual(suggest_company_slug("@@@ !!! ???"), [])

    def test_non_latin_name(self):
        print("✓ test_non_latin_name: ignores non-Latin names")
        self.assertEqual(suggest_company_slug("株式会社テスト"), [])

    def test_one_valid_word_others_invalid(self):
        print("✓ test_one_valid_word_others_invalid: considers only the valid parts")
        self.assertEqual(suggest_company_slug("Tech @@@"), ["tech"])
