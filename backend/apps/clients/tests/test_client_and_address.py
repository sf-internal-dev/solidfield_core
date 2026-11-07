from django.test import TestCase
from django.db import IntegrityError
from backend.apps.core.models import CompanyTenant
from backend.apps.clients.models import Client, ClientAddress

class ClientModelTest(TestCase):
    def setUp(self):
        print("→ setUp: Creating tenant and client for tests...")
        self.tenant = CompanyTenant.objects.create(name="Client Tenant", slug="tenant-client")
        self.client = Client.objects.create(
            tenant=self.tenant,
            person_type="company",
            name="Company XPTO",
            document_id="1234567890001",
            contact_name="Fulano",
            phone="(11) 99999-9999",
            email="contact@company.com"
        )

    def test_client_str(self):
        print("✓ test_client_str: __str__ should return the client name")
        self.assertEqual(str(self.client), "Company XPTO")

    def test_unique_document_per_tenant(self):
        print("✓ test_unique_document_per_tenant: Should fail if document_id repeats in the same tenant")
        with self.assertRaises(IntegrityError):
            Client.objects.create(
                tenant=self.tenant,
                person_type="company",
                name="Clone Company",
                document_id="1234567890001",  # same document
                contact_name="Ciclano",
                phone="(11) 88888-8888",
                email="other@company.com"
            )

    def test_same_document_different_tenants(self):
        print("✓ test_same_document_different_tenants: Same document_id allowed in different tenants")
        another_tenant = CompanyTenant.objects.create(name="Tenant B", slug="tenant-b")
        client_b = Client.objects.create(
            tenant=another_tenant,
            person_type="company",
            name="Company B",
            document_id="1234567890001",  # same document
            contact_name="Beltrano",
            phone="(21) 99999-0000",
            email="b@company.com"
        )
        self.assertEqual(client_b.document_id, "1234567890001")

class ClientAddressModelTest(TestCase):
    def setUp(self):
        print("→ setUp: Creating client and address for tests...")
        self.tenant = CompanyTenant.objects.create(name="Address Tenant", slug="tenant-end")
        self.client = Client.objects.create(
            tenant=self.tenant,
            person_type="individual",
            name="Maria da Silva",
            document_id="99999999999",
            contact_name="Maria",
            phone="(31) 91234-5678",
            email="maria@example.com"
        )
        self.address = ClientAddress.objects.create(
            client=self.client,
            label="Residence",
            street="Street A",
            number="123",
            complement="House 1",
            neighborhood="Downtown",
            city="Belo Horizonte",
            state="MG",
            zip_code="30100-000",
            gps_latitude=-19.915,
            gps_longitude=-43.938
        )

    def test_address_str(self):
        print("✓ test_address_str: __str__ should return 'label - city'")
        self.assertEqual(str(self.address), "Residence - Belo Horizonte")

    def test_address_relationship(self):
        print("✓ test_address_relationship: Client should access its addresses through the related_name")
        self.assertIn(self.address, self.client.addresses.all())
