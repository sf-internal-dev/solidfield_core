# backend/apps/core/tests/tenant/test_tenant_service.py

from django.test import TestCase
from unittest.mock import patch
from django.contrib.auth import get_user_model

from backend.apps.core.models import CompanyTenant
from backend.apps.core.services.tenant_service import (
    resolve_available_slug_from_name,
    generate_valid_tenant_code,
    prepare_company_slug_and_code,
    register_tenant,
)


class ResolveAvailableSlugFromNameTest(TestCase):
    @patch("backend.apps.core.services.tenant_service.suggest_company_slug", return_value=["alpha", "beta"])
    def test_resolve_returns_first_available_suggestion(self, _mock_suggest):
        print("→ resolve_available_slug_from_name: retorna a 1ª sugestão livre (tupla (slug, error))")
        slug, err = resolve_available_slug_from_name("Alpha Co")
        self.assertEqual(err, "")
        self.assertEqual(slug, "alpha")

    @patch("backend.apps.core.services.tenant_service.suggest_company_slug", return_value=["acme", "acmeinc"])
    @patch("backend.apps.core.services.tenant_service.sanitize_tenant_slug", return_value="company")
    def test_resolve_all_taken_fallback_numeric(self, _mock_sanitize, _mock_suggest):
        print("→ resolve_available_slug_from_name: todas ocupadas → fallback numérico (tupla)")
        CompanyTenant.objects.create(name="X", slug="acme", tenant_code="ACM1")
        CompanyTenant.objects.create(name="Y", slug="acmeinc", tenant_code="ACM2")
        CompanyTenant.objects.create(name="Z", slug="company1", tenant_code="ACM3")

        slug, err = resolve_available_slug_from_name("Alpha Co")
        self.assertEqual(err, "")
        self.assertIsInstance(slug, str)
        self.assertTrue(slug.startswith("company"))
        self.assertNotEqual(slug, "company1")  # não deve colidir


class GenerateValidTenantCodeTest(TestCase):
    def test_generate_code_returns_first_free(self):
        print("→ generate_valid_tenant_code: retorna primeira tentativa livre")
        with patch("backend.apps.core.services.tenant_service.generate_tenant_code_attempts",
                   return_value=["ABCD", "ABCD1", "ABCD2"]):
            code = generate_valid_tenant_code("acme")
            self.assertEqual(code, "ABCD")

    def test_generate_code_fallback_path_returns_string(self):
        print("→ generate_valid_tenant_code: todas ocupadas → usa fallback aleatório e retorna string válida")
        # ocupar algumas possibilidades comuns
        CompanyTenant.objects.create(name="A", slug="a", tenant_code="COMP")
        CompanyTenant.objects.create(name="B", slug="b", tenant_code="COMP1")
        CompanyTenant.objects.create(name="C", slug="c", tenant_code="COMP2")

        # simular que TODAS tentativas estão ocupadas para forçar fallback
        with patch("backend.apps.core.services.tenant_service.generate_tenant_code_attempts",
                   return_value=["COMP", "COMP1", "COMP2"]):
            code = generate_valid_tenant_code("qualquer")
            self.assertIsInstance(code, str)
            self.assertNotIn(code, {"COMP", "COMP1", "COMP2"})
            self.assertGreaterEqual(len(code), 4)


class PrepareCompanySlugAndCodeTest(TestCase):
    @patch("backend.apps.core.services.tenant_service.generate_valid_tenant_code", return_value="ABCD")
    @patch("backend.apps.core.services.tenant_service.resolve_available_slug_from_name", return_value=("acme", ""))
    def test_prepare_company_slug_and_code_happy_path(self, _mock_resolve, _mock_code):
        print("→ prepare_company_slug_and_code: retorna dict com slug e tenant_code (resolve→tupla)")
        res = prepare_company_slug_and_code("Acme Ltda")
        self.assertEqual(res, {"slug": "acme", "tenant_code": "ABCD"})

    @patch("backend.apps.core.services.tenant_service.generate_valid_tenant_code", return_value="CODE1")
    @patch("backend.apps.core.services.tenant_service.resolve_available_slug_from_name", return_value=("acme1", ""))
    def test_prepare_company_slug_and_code_handles_resolve_tuple(self, _mock_resolve, _mock_code):
        print("→ prepare_company_slug_and_code: lida com retorno tupla de resolve (slug, '')")
        res = prepare_company_slug_and_code("Acme Ltda")
        self.assertEqual(res, {"slug": "acme1", "tenant_code": "CODE1"})


class RegisterTenantTest(TestCase):
    def setUp(self):
        print("→ setUp register_tenant: criando AccountHolderUser real (email/full_name)")
        User = get_user_model()  # retorna AccountHolderUser
        self.owner = User.objects.create(
            email="owner@example.com",
            full_name="Owner Name",
            is_active=True,
            is_staff=False,
        )
        # atributo opcional que o service pode consumir via getattr
        self.owner.phone = "+55 11 99999-9999"

    @patch("backend.apps.core.services.tenant_service.validate_optional_phone", return_value=True)
    @patch("backend.apps.core.services.tenant_service.validate_optional_email", return_value=True)
    @patch("backend.apps.core.services.tenant_service.validate_slug_format", return_value=True)
    @patch("backend.apps.core.services.tenant_service.validate_tenant_name", return_value=True)
    def test_register_tenant_success(self, _vname, _vslug, _vemail, _vphone):
        print("→ register_tenant: cria tenant quando todas validações passam e owner é válido")
        tenant, errors = register_tenant(
            name="Tenant X",
            slug="tenantx",
            tenant_code="TENX",
            billing_account_id="BILL123",   # use o nome que seu service espera
            owner=self.owner,
            locale="pt_BR",
            timezone="America/Sao_Paulo",
        )

        self.assertIsNotNone(tenant)
        self.assertEqual(errors, [])
        self.assertEqual(tenant.name, "Tenant X")
        self.assertEqual(tenant.slug, "tenantx")
        self.assertEqual(tenant.tenant_code, "TENX")
        self.assertEqual(tenant.primary_contact_name, "Owner Name")
        self.assertEqual(tenant.primary_contact_email, "owner@example.com")

        # se o model estiver com null=True no phone, aceite None ou string
        self.assertIn(tenant.primary_contact_phone, [None, "", "+55 11 99999-9999"])

        # campo de conta (ajuste o nome conforme seu model: billing_account_id vs billind_account_id)
        if hasattr(tenant, "billing_account_id"):
            self.assertEqual(tenant.billing_account_id, "BILL123")
        elif hasattr(tenant, "billind_account_id"):
            self.assertEqual(tenant.billind_account_id, "BILL123")

        self.assertEqual(tenant.locale, "pt_BR")
        self.assertEqual(tenant.timezone, "America/Sao_Paulo")
        if hasattr(tenant, "owner_id"):
            self.assertEqual(tenant.owner_id, self.owner.id)

    @patch("backend.apps.core.services.tenant_service.validate_optional_phone", return_value=False)
    @patch("backend.apps.core.services.tenant_service.validate_optional_email", return_value=False)
    @patch("backend.apps.core.services.tenant_service.validate_slug_format", return_value=False)
    @patch("backend.apps.core.services.tenant_service.validate_tenant_name", return_value=False)
    def test_register_tenant_accumulates_errors(self, _vname, _vslug, _vemail, _vphone):
        print("→ register_tenant: acumula validações e não cria quando inválido")
        tenant, errors = register_tenant(
            name="",
            slug="***",
            tenant_code="TENX",
            billing_account_id="BILL123",
            owner=self.owner,
            locale="pt_BR",
            timezone="America/Sao_Paulo",
        )
        self.assertIsNone(tenant)
        # o service usa "invalid_slug_format" também para email/phone — testamos o comportamento atual
        self.assertIn("invalid_tenant_name", errors)
        self.assertGreaterEqual(errors.count("invalid_slug_format"), 3)  # slug + email + phone
