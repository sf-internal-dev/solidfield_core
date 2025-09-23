from django.test import TestCase
from unittest.mock import patch

from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.core.services import technician_registration_service  # ajuste se o register_technician estiver em outro módulo


class RegisterTechnicianServiceTestCase(TestCase):
    def setUp(self):
        print("→ setUp: criando tenant e técnico operador")
        self.tenant = CompanyTenant.objects.create(name="TenantTech", slug="tenant-tech")

        # técnico operador L3 (gerente)
        self.operating = Technician.objects.create(
            tenant=self.tenant,
            username="operador",
            social_name="Manager",
            technician_permission="L3",
        )

    # ----------------------------
    # caso 1: permissão negada
    # ----------------------------
    @patch("backend.apps.core.services.technician_registration_service.has_permission")
    def test_permission_denied(self, mock_perm):
        print("✓ register_technician: falha se operador não tem permissão")
        mock_perm.return_value = (False, ["no_permission"])

        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="u1",
            social_name="Nome Válido",
            technician_permission="L1",
        )
        self.assertIsNone(tech)
        self.assertIn("no_permission", errors)
        self.assertEqual(Technician.objects.count(), 1)  # só o operador existe

    # ----------------------------
    # caso 2: validações falham
    # ----------------------------
    @patch("backend.apps.core.services.technician_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technician_registration_service.validate_social_name", return_value=False)
    @patch("backend.apps.core.services.technician_registration_service.validate_username", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_technician_permission", return_value=True)
    def test_invalid_social_name(self, m1, m2, m3, m4):
        print("✓ register_technician: falha se social_name inválido")
        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="u1",
            social_name="??",
            technician_permission="L1",
        )
        self.assertIsNone(tech)
        self.assertIn("invalid_social_name", errors)

    @patch("backend.apps.core.services.technician_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technician_registration_service.validate_social_name", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_username", return_value=False)
    @patch("backend.apps.core.services.technician_registration_service.validate_technician_permission", return_value=True)
    def test_invalid_username(self, m1, m2, m3, m4):
        print("✓ register_technician: falha se username inválido")
        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="",
            social_name="Nome Válido",
            technician_permission="L1",
        )
        self.assertIsNone(tech)
        self.assertIn("invalid_usename", errors)  # cuidado: tem typo no service

    @patch("backend.apps.core.services.technician_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technician_registration_service.validate_social_name", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_username", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_technician_permission", return_value=False)
    def test_invalid_permission_level(self, m1, m2, m3, m4):
        print("✓ register_technician: falha se technician_permission inválido")
        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="u2",
            social_name="Nome Válido",
            technician_permission="XXX",
        )
        self.assertIsNone(tech)
        self.assertIn("invalid_technician_permission", errors)

    # ----------------------------
    # caso 3: sucesso
    # ----------------------------
    @patch("backend.apps.core.services.technician_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technician_registration_service.validate_social_name", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_username", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_technician_permission", return_value=True)
    def test_register_success(self, m1, m2, m3, m4):
        print("✓ register_technician: cria técnico válido")
        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="tec01",
            social_name="Tec Nome",
            technician_permission="L1",
        )
        self.assertIsNotNone(tech)
        self.assertEqual(errors, [])
        self.assertEqual(tech.username, "tec01")
        self.assertTrue(tech.is_active)
        self.assertEqual(Technician.objects.count(), 2)  # operador + novo

    # ----------------------------
    # caso 4: múltiplos erros
    # ----------------------------
    @patch("backend.apps.core.services.technician_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technician_registration_service.validate_social_name", return_value=False)
    @patch("backend.apps.core.services.technician_registration_service.validate_username", return_value=False)
    @patch("backend.apps.core.services.technician_registration_service.validate_technician_permission", return_value=False)
    def test_multiple_errors(self, m1, m2, m3, m4):
        print("✓ register_technician: acumula múltiplos erros de validação")
        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="",
            social_name="",
            technician_permission="XXX",
        )
        self.assertIsNone(tech)
        self.assertIn("invalid_social_name", errors)
        self.assertIn("invalid_usename", errors)  # com typo
        self.assertIn("invalid_technician_permission", errors)
