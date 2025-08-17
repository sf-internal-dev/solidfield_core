from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.clients.models import Client
from backend.apps.orders.models import WorkOrder
from backend.apps.filehub.models import WorkOrderPhoto

class WorkOrderPhotoTest(TestCase):
    def setUp(self):
        print("→ setUp: Criando tenant, técnico, cliente e OS para teste de foto...")
        self.tenant = CompanyTenant.objects.create(name="TenantPhoto", slug="tenant-photo")

        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="tech_photo",
            social_name="Foto Tech",
            technician_permission="L2"
        )

        self.client = Client.objects.create(
            tenant=self.tenant,
            name="Cliente Foto",
            person_type="company",
            document_id="11987654321"
        )

        self.order = WorkOrder.objects.create(
            tenant=self.tenant,
            identifier="OS-FOTO-001",
            created_by=self.tech,
            assigned_to=self.tech,
            client=self.client
        )

        self.fake_image = SimpleUploadedFile(
            "foto.jpg",
            b"filecontent",
            content_type="image/jpeg"
        )

    def test_photo_creation_with_minimum_fields(self):
        print("✓ test_photo_creation_with_minimum_fields: Criando foto com campos obrigatórios")
        photo = WorkOrderPhoto.objects.create(
            service_order=self.order,
            uploaded_by=self.tech,
            image=self.fake_image,
            photo_type="before"
        )
        self.assertEqual(photo.photo_type, "before")
        self.assertTrue(photo.image.name.startswith("service_photos/"))
        self.assertEqual(photo.service_order, self.order)

    def test_str_representation(self):
        print("✓ test_str_representation: __str__ deve incluir ordem, tipo de foto e técnico")
        photo = WorkOrderPhoto.objects.create(
            service_order=self.order,
            uploaded_by=self.tech,
            image=self.fake_image,
            photo_type="after"
        )
        expected_str = f"{self.order.identifier} - after by {self.tech}"
        self.assertEqual(str(photo), expected_str)

    def test_optional_fields(self):
        print("✓ test_optional_fields: Deve permitir salvar descrição, gps e device_info")
        photo = WorkOrderPhoto.objects.create(
            service_order=self.order,
            uploaded_by=self.tech,
            image=self.fake_image,
            photo_type="custom",
            description="Área isolada",
            gps_latitude=-23.5505,
            gps_longitude=-46.6333,
            device_info="Xiaomi Redmi Note"
        )
        self.assertEqual(photo.description, "Área isolada")
        self.assertAlmostEqual(photo.gps_latitude, -23.5505)
        self.assertIn("Xiaomi", photo.device_info)

    def test_uploaded_at_auto_set(self):
        print("✓ test_uploaded_at_auto_set: Campo uploaded_at deve ser preenchido automaticamente")
        photo = WorkOrderPhoto.objects.create(
            service_order=self.order,
            uploaded_by=self.tech,
            image=self.fake_image,
            photo_type="proof"
        )
        self.assertLessEqual(photo.uploaded_at, timezone.now())
