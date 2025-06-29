from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.clients.models import Client
from backend.apps.orders.models import ServiceOrder
from backend.apps.filehub.models import ServiceOrderSignature

class ServiceOrderSignatureTest(TestCase):
    def setUp(self):
        print("→ setUp: Criando tenant, técnico, cliente e ordem para teste de assinatura...")
        self.tenant = CompanyTenant.objects.create(name="TenantSignature", slug="tenant-signature")

        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="signtech",
            social_name="Sign Tech",
            technician_permission="L2"
        )

        self.client = Client.objects.create(
            tenant=self.tenant,
            name="Cliente Assinatura",
            person_type="company",
            document_id="55555555555"
        )

        self.order = ServiceOrder.objects.create(
            tenant=self.tenant,
            identifier="OS-SIGN-001",
            created_by=self.tech,
            assigned_to=self.tech,
            client=self.client
        )

        self.fake_signature = SimpleUploadedFile(
            "assinatura.png",
            b"filecontent",
            content_type="image/png"
        )

    def test_create_signature_minimum_fields(self):
        print("✓ test_create_signature_minimum_fields: Criando assinatura com campos mínimos")
        signature = ServiceOrderSignature.objects.create(
            service_order=self.order,
            ordered_by=self.tech,
            signed_by="Cliente X",
            image=self.fake_signature
        )
        self.assertEqual(signature.signed_by, "Cliente X")
        self.assertEqual(signature.ordered_by, self.tech)
        self.assertTrue(signature.image.name.startswith("signatures/"))

    def test_str_representation(self):
        print("✓ test_str_representation: __str__ deve conter identificador, nome e técnico")
        signature = ServiceOrderSignature.objects.create(
            service_order=self.order,
            ordered_by=self.tech,
            signed_by="Joana",
            image=self.fake_signature
        )
        expected_str = f"{self.order.identifier} - signed by Joana - ordered by {self.tech}"
        self.assertEqual(str(signature), expected_str)

    def test_optional_fields(self):
        print("✓ test_optional_fields: Deve aceitar latitude, longitude e IP opcionalmente")
        signature = ServiceOrderSignature.objects.create(
            service_order=self.order,
            ordered_by=self.tech,
            signed_by="Cliente Geo",
            image=self.fake_signature,
            latitude=-22.9068,
            longitude=-43.1729,
            ip_address="192.168.0.1"
        )
        self.assertEqual(signature.latitude, -22.9068)
        self.assertEqual(signature.ip_address, "192.168.0.1")

    def test_signed_at_auto_set(self):
        print("✓ test_signed_at_auto_set: signed_at deve ser preenchido automaticamente")
        signature = ServiceOrderSignature.objects.create(
            service_order=self.order,
            ordered_by=self.tech,
            signed_by="Automático",
            image=self.fake_signature
        )
        self.assertLessEqual(signature.signed_at, timezone.now())
