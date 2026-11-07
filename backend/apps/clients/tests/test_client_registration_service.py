# backend/apps/clients/tests/test_client_registration_service.py

from django.test import TestCase
from unittest.mock import patch

from backend.apps.core.models import CompanyTenant
from backend.apps.core.models.technician import Technician
from backend.apps.clients.models.client import Client, ClientAddress

from backend.apps.clients.services.client_registration_service import (
    create_or_update_client,
    register_client_address,
)


class CreateOrUpdateClientServiceTest(TestCase):
    def setUp(self):
        print("→ setUp: creating tenant and technician")
        self.tenant = CompanyTenant.objects.create(name="T1", slug="t1", tenant_code="T1AA")
        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="tech01",
            social_name="Tech One",
            technician_permission="L3",
            is_active=True,
        )

    @patch("backend.apps.clients.services.client_registration_service.has_permission", return_value=(False, ["no_perm"]))
    def test_permission_denied_returns_none_and_errors(self, _perm):
        print("✓ create_or_update_client: no permission → None + 'no_perm'")
        client, errors = create_or_update_client(
            technician_operating=self.tech,
            name="Acme",
            person_type="company",
            country="US",
        )
        self.assertIsNone(client)
        self.assertEqual(errors, ["no_perm"])

    @patch("backend.apps.clients.services.client_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.clients.services.client_registration_service.validate_email_field", return_value=True)
    @patch("backend.apps.clients.services.client_registration_service.validate_phone_number", return_value=True)
    @patch("backend.apps.clients.services.client_registration_service.validate_document_id", return_value=True)
    @patch("backend.apps.clients.services.client_registration_service.validate_contact_name", return_value=(True, []))
    @patch("backend.apps.clients.services.client_registration_service.validate_name", return_value=(True, []))
    def test_create_new_client_success(self, _vname, _vcontact, _vdoc, _vphone, _vemail, _perm):
        print("✓ create_or_update_client: creates a client when every validation passes")
        client, errors = create_or_update_client(
            technician_operating=self.tech,
            person_type="company",
            name="Acme Inc",
            document_id="123-45-6789",
            contact_name="Alice",
            phone="+11234567890",
            email="alice@acme.com",
            country="US",
        )
        self.assertIsNotNone(client)
        self.assertEqual(errors, [])
        self.assertEqual(Client.objects.count(), 1)
        cdb = Client.objects.get(pk=client.pk)
        self.assertEqual(cdb.person_type, "company")
        self.assertEqual(cdb.name, "Acme Inc")
        self.assertEqual(cdb.document_id, "123-45-6789")
        self.assertEqual(cdb.contact_name, "Alice")
        self.assertEqual(cdb.phone, "+11234567890")
        self.assertEqual(cdb.email, "alice@acme.com")
        self.assertEqual(cdb.tenant_id, self.tenant.id)

    @patch("backend.apps.clients.services.client_registration_service.has_permission", return_value=(True, ""))
    @patch("backend.apps.clients.services.client_registration_service.validate_email_field", return_value=False)
    @patch("backend.apps.clients.services.client_registration_service.validate_phone_number", return_value=False)
    @patch("backend.apps.clients.services.client_registration_service.validate_document_id", return_value=False)
    @patch("backend.apps.clients.services.client_registration_service.validate_contact_name", return_value=(False, ["invalid_contact_name"]))
    @patch("backend.apps.clients.services.client_registration_service.validate_name", return_value=(False, ["invalid_name"]))
    def test_create_new_client_accumulates_errors_and_does_not_save(self, _vname, _vcontact, _vdoc, _vphone, _vemail, _perm):
        print("✓ create_or_update_client: accumulates errors; does not persist if there are errors")
        client, errors = create_or_update_client(
            technician_operating=self.tech,
            person_type="invalid",  # produces invalid_person_type
            name="@@",              # invalid_name
            document_id="bad",
            contact_name="",
            phone="bad",
            email="bad",
            country="US",
        )
        # returns the created instance (not saved)
        self.assertIsInstance(client, Client)
        self.assertIn("invalid_person_type", errors)
        self.assertIn("invalid_name", errors)
        self.assertIn("invalid_document_id", errors)
        self.assertIn("invalid_phone_number", errors)
        self.assertIn("invalid_email", errors)
        self.assertEqual(Client.objects.count(), 0)

    @patch("backend.apps.clients.services.client_registration_service.has_permission", return_value=(True, ""))
    @patch("backend.apps.clients.services.client_registration_service.validate_email_field", return_value=False)
    @patch("backend.apps.clients.services.client_registration_service.validate_phone_number", return_value=True)
    @patch("backend.apps.clients.services.client_registration_service.validate_document_id", return_value=True)
    @patch("backend.apps.clients.services.client_registration_service.validate_contact_name", return_value=(True, []))
    @patch("backend.apps.clients.services.client_registration_service.validate_name", return_value=(True, []))
    def test_update_existing_client_partial_with_errors_does_not_save(self, _vname, _vcontact, _vdoc, _vphone, _vemail, _perm):
        print("✓ create_or_update_client: partial update with an error → does not save changes")
        existing = Client.objects.create(
            tenant=self.tenant,
            person_type="company",
            name="Old",
            document_id="123456789",
            contact_name="Bob",
            phone="+11234567890",
            email="old@acme.com",
        )
        client, errors = create_or_update_client(
            technician_operating=self.tech,
            client=existing,
            name="New Name",
            email="invalid-email",  # invalid
            country="US",
        )
        self.assertIsInstance(client, Client)
        self.assertIn("invalid_email", errors)
        existing.refresh_from_db()
        self.assertEqual(existing.name, "Old")
        self.assertEqual(existing.email, "old@acme.com")

    @patch("backend.apps.clients.services.client_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.clients.services.client_registration_service.validate_email_field", return_value=True)
    @patch("backend.apps.clients.services.client_registration_service.validate_phone_number", return_value=True)
    @patch("backend.apps.clients.services.client_registration_service.validate_document_id", return_value=True)
    @patch("backend.apps.clients.services.client_registration_service.validate_contact_name", return_value=(True, []))
    @patch("backend.apps.clients.services.client_registration_service.validate_name", return_value=(True, []))
    def test_update_existing_client_success_saves(self, _vname, _vcontact, _vdoc, _vphone, _vemail, _perm):
        print("✓ create_or_update_client: update with no errors → saves")
        existing = Client.objects.create(
            tenant=self.tenant,
            person_type="company",
            name="Old",
            document_id="123456789",
            contact_name="Bob",
            phone="+11234567890",
            email="old@acme.com",
        )
        client, errors = create_or_update_client(
            technician_operating=self.tech,
            client=existing,
            name="New Name",
            email="new@acme.com",
            country="US",
        )
        self.assertEqual(errors, [])
        existing.refresh_from_db()
        self.assertEqual(existing.name, "New Name")
        self.assertEqual(existing.email, "new@acme.com")


class RegisterClientAddressServiceTest(TestCase):
    def setUp(self):
        print("→ setUp address: creating tenant, technician, and client")
        self.tenant = CompanyTenant.objects.create(name="T2", slug="t2", tenant_code="T2AA")
        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="tech02",
            social_name="Tech Two",
            technician_permission="L3",
            is_active=True,
        )
        self.client = Client.objects.create(
            tenant=self.tenant,
            person_type="company",
            name="Client Co",
        )

    @patch("backend.apps.clients.services.client_registration_service.has_permission", return_value=(False, "no_perm"))
    def test_permission_denied(self, _perm):
        print("✓ register_client_address: no permission → None + 'no_perm'")
        addr, errors = register_client_address(
            technician_operating=self.tech,
            client=self.client,
            code="12345",
            state="CA",
            country="US",
            lat=0.0,
            lng=0.0,
            label="HQ",
            city="LA",
        )
        self.assertIsNone(addr)
        self.assertEqual(errors, "no_perm")

    @patch("backend.apps.clients.services.client_registration_service.has_permission", return_value=(True, ""))
    @patch("backend.apps.clients.services.client_registration_service.validate_coordinates", return_value=False)
    @patch("backend.apps.clients.services.client_registration_service.validate_region_code", return_value=False)
    @patch("backend.apps.clients.services.client_registration_service.validate_postal_code", return_value=False)
    def test_validation_errors_accumulate(self, _vzip, _vstate, _vcoords, _perm):
        print("✓ register_client_address: accumulates postal code, region, and coordinate errors")
        addr, errors = register_client_address(
            technician_operating=self.tech,
            client=self.client,
            code="BAD",
            state="??",
            country="US",
            lat=999,
            lng=999,
            label="HQ",
            city="Nowhere",
        )
        self.assertIsNone(addr)
        self.assertIn("invalid_postal_code", errors)
        self.assertIn("invalid_region_code", errors)
        self.assertIn("invalid_coordinates", errors)
        self.assertEqual(ClientAddress.objects.count(), 0)

    @patch("backend.apps.clients.services.client_registration_service.has_permission", return_value=(True, []))
    @patch("backend.apps.clients.services.client_registration_service.validate_coordinates", return_value=True)
    @patch("backend.apps.clients.services.client_registration_service.validate_region_code", return_value=True)
    @patch("backend.apps.clients.services.client_registration_service.validate_postal_code", return_value=True)
    def test_success_creates_address(self, _vzip, _vstate, _vcoords, _perm):
        print("✓ register_client_address: success → creates the address and returns '' in errors")
        addr, errors = register_client_address(
            technician_operating=self.tech,
            client=self.client,
            code="12345",
            state="CA",
            country="US",
            lat=34.05,
            lng=-118.24,
            label="HQ",
            street="Main St",
            number="100",
            complement="Suite 10",
            neighborhood="Central",
            city="Los Angeles",
        )
        self.assertIsNotNone(addr)
        self.assertEqual(errors, [])
        self.assertEqual(ClientAddress.objects.count(), 1)
        adb = ClientAddress.objects.get(pk=addr.pk)
        self.assertEqual(adb.client_id, self.client.id)
        self.assertEqual(adb.label, "HQ")
        self.assertEqual(adb.street, "Main St")
        self.assertEqual(adb.number, "100")
        self.assertEqual(adb.complement, "Suite 10")
        self.assertEqual(adb.neighborhood, "Central")
        self.assertEqual(adb.city, "Los Angeles")
        self.assertEqual(adb.state, "CA")
        self.assertEqual(adb.postal_code, "12345")
        self.assertEqual(float(adb.gps_latitude), 34.05)
        self.assertEqual(float(adb.gps_longitude), -118.24)
