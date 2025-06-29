from django.test import TestCase
from django.db import IntegrityError
from backend.apps.core.models import CompanyTenant
from backend.apps.clients.models import Client, ClientAddress

class ClientModelTest(TestCase):
    def setUp(self):
        print("→ setUp: Criando tenant e cliente para testes...")
        self.tenant = CompanyTenant.objects.create(name="TenantCliente", slug="tenant-cliente")
        self.client = Client.objects.create(
            tenant=self.tenant,
            person_type="company",
            name="Empresa XPTO",
            document_id="1234567890001",
            contact_name="Fulano",
            phone="(11) 99999-9999",
            email="contato@empresa.com"
        )

    def test_client_str(self):
        print("✓ test_client_str: __str__ deve retornar o nome do cliente")
        self.assertEqual(str(self.client), "Empresa XPTO")

    def test_unique_document_per_tenant(self):
        print("✓ test_unique_document_per_tenant: Deve falhar se document_id repetir no mesmo tenant")
        with self.assertRaises(IntegrityError):
            Client.objects.create(
                tenant=self.tenant,
                person_type="company",
                name="Empresa Clone",
                document_id="1234567890001",  # mesmo documento
                contact_name="Ciclano",
                phone="(11) 88888-8888",
                email="outro@empresa.com"
            )

    def test_same_document_different_tenants(self):
        print("✓ test_same_document_different_tenants: Mesmo document_id permitido em tenants diferentes")
        another_tenant = CompanyTenant.objects.create(name="Tenant B", slug="tenant-b")
        client_b = Client.objects.create(
            tenant=another_tenant,
            person_type="company",
            name="Empresa B",
            document_id="1234567890001",  # mesmo doc
            contact_name="Beltrano",
            phone="(21) 99999-0000",
            email="b@empresa.com"
        )
        self.assertEqual(client_b.document_id, "1234567890001")

class ClientAddressModelTest(TestCase):
    def setUp(self):
        print("→ setUp: Criando cliente e endereço para testes...")
        self.tenant = CompanyTenant.objects.create(name="Tenant Endereço", slug="tenant-end")
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
            label="Residência",
            street="Rua A",
            number="123",
            complement="Casa 1",
            neighborhood="Centro",
            city="Belo Horizonte",
            state="MG",
            zip_code="30100-000",
            gps_latitude=-19.915,
            gps_longitude=-43.938
        )

    def test_address_str(self):
        print("✓ test_address_str: __str__ deve retornar 'label - city'")
        self.assertEqual(str(self.address), "Residência - Belo Horizonte")

    def test_address_relationship(self):
        print("✓ test_address_relationship: Cliente deve acessar seus endereços pelo related_name")
        self.assertIn(self.address, self.client.addresses.all())
