from django.test import TestCase
from unittest.mock import patch

from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.core.services import technician_registration_service  # adjust if register_technician lives in another module


class RegisterTechnicianServiceTestCase(TestCase):
    def setUp(self):
        print("→ setUp: creating tenant and operating technician")
        self.tenant = CompanyTenant.objects.create(name="TenantTech", slug="tenant-tech")

        # operating L3 technician (manager)
        self.operating = Technician.objects.create(
            tenant=self.tenant,
            username="operator",
            social_name="Manager",
            technician_permission="L3",
        )

    # ----------------------------
    # case 1: permission denied
    # ----------------------------
    @patch("backend.apps.core.services.technician_registration_service.has_permission")
    def test_permission_denied(self, mock_perm):
        print("✓ register_technician: fails if the operator has no permission")
        mock_perm.return_value = (False, ["no_permission"])

        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="u1",
            social_name="Valid Name",
            technician_permission="L1",
        )
        self.assertIsNone(tech)
        self.assertIn("no_permission", errors)
        self.assertEqual(Technician.objects.count(), 1)  # only the operator exists

    # ----------------------------
    # case 2: validations fail
    # ----------------------------
    @patch("backend.apps.core.services.technician_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technician_registration_service.validate_social_name", return_value=False)
    @patch("backend.apps.core.services.technician_registration_service.validate_username", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_technician_permission", return_value=True)
    def test_invalid_social_name(self, m1, m2, m3, m4):
        print("✓ register_technician: fails if social_name is invalid")
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
        print("✓ register_technician: fails if username is invalid")
        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="",
            social_name="Valid Name",
            technician_permission="L1",
        )
        self.assertIsNone(tech)
        self.assertIn("invalid_usename", errors)  # careful: the service has a typo

    @patch("backend.apps.core.services.technician_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technician_registration_service.validate_social_name", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_username", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_technician_permission", return_value=False)
    def test_invalid_permission_level(self, m1, m2, m3, m4):
        print("✓ register_technician: fails if technician_permission is invalid")
        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="u2",
            social_name="Valid Name",
            technician_permission="XXX",
        )
        self.assertIsNone(tech)
        self.assertIn("invalid_technician_permission", errors)

    # ----------------------------
    # case 3: success
    # ----------------------------
    @patch("backend.apps.core.services.technician_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technician_registration_service.validate_social_name", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_username", return_value=True)
    @patch("backend.apps.core.services.technician_registration_service.validate_technician_permission", return_value=True)
    def test_register_success(self, m1, m2, m3, m4):
        print("✓ register_technician: creates a valid technician")
        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="tec01",
            social_name="Tech Name",
            technician_permission="L1",
        )
        self.assertIsNotNone(tech)
        self.assertEqual(errors, [])
        self.assertEqual(tech.username, "tec01")
        self.assertTrue(tech.is_active)
        self.assertEqual(Technician.objects.count(), 2)  # operator + new one

    # ----------------------------
    # case 4: multiple errors
    # ----------------------------
    @patch("backend.apps.core.services.technician_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.core.services.technician_registration_service.validate_social_name", return_value=False)
    @patch("backend.apps.core.services.technician_registration_service.validate_username", return_value=False)
    @patch("backend.apps.core.services.technician_registration_service.validate_technician_permission", return_value=False)
    def test_multiple_errors(self, m1, m2, m3, m4):
        print("✓ register_technician: accumulates multiple validation errors")
        tech, errors = technician_registration_service.register_technician(
            technician_operating=self.operating,
            username="",
            social_name="",
            technician_permission="XXX",
        )
        self.assertIsNone(tech)
        self.assertIn("invalid_social_name", errors)
        self.assertIn("invalid_usename", errors)  # with the typo
        self.assertIn("invalid_technician_permission", errors)
