from django.test import TestCase
from django.utils import timezone
from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.clients.models import Client
from backend.apps.orders.models import ServiceOrder
from backend.apps.clients.models import ClientFeedback, FeedbackLink

class ClientFeedbackAndLinkTest(TestCase):
    def setUp(self):
        print("→ setUp: Creating tenant, technician, client, and work order...")
        self.tenant = CompanyTenant.objects.create(name="TenantFeedback", slug="tenant-feedback")
        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="feedtech",
            social_name="Feedback Tech",
            technician_permission="L1"
        )
        self.client = Client.objects.create(
            tenant=self.tenant,
            name="Test Client",
            person_type="individual",
            document_id="00011122233"
        )
        self.order = ServiceOrder.objects.create(
            tenant=self.tenant,
            identifier="OSFB001",
            created_by=self.tech,
            assigned_to=self.tech,
            client=self.client
        )

    def test_create_feedback_with_client(self):
        print("✓ test_create_feedback_with_client: Creating feedback with a linked client")
        feedback = ClientFeedback.objects.create(
            service_order=self.order,
            client=self.client,
            client_name="Client Name",
            client_email="client@test.com",
            stars=5,
            comment="Great service",
            strengths="Promptness, courtesy"
        )
        self.assertEqual(feedback.stars, 5)
        self.assertEqual(feedback.client, self.client)
        self.assertIn("Great", feedback.comment)
        self.assertIsNotNone(feedback.submitted_at)

    def test_create_feedback_without_client(self):
        print("✓ test_create_feedback_without_client: Creating feedback without a linked client")
        feedback = ClientFeedback.objects.create(
            service_order=self.order,
            stars=3,
            client_name="Anonymous",
            comment="Good, but it can improve"
        )
        self.assertEqual(feedback.client, None)
        self.assertEqual(feedback.client_name, "Anonymous")

    def test_feedback_submitted_at_auto(self):
        print("✓ test_feedback_submitted_at_auto: Field submitted_at should be filled in automatically")
        feedback = ClientFeedback.objects.create(
            service_order=self.order,
            stars=4
        )
        self.assertIsNotNone(feedback.submitted_at)
        self.assertLessEqual(feedback.submitted_at, timezone.now())

    def test_feedback_link_key_autogeneration(self):
        print("✓ test_feedback_link_key_autogeneration: Should generate a key automatically on save")
        link = FeedbackLink.objects.create(service_order=self.order)
        self.assertTrue(link.key)
        self.assertTrue(16 <= len(link.key) <= 20)


    def test_feedback_link_uniqueness(self):
        print("✓ test_feedback_link_uniqueness: Key should be unique")
        link1 = FeedbackLink.objects.create(service_order=self.order)
        with self.assertRaises(Exception):
            FeedbackLink.objects.create(service_order=self.order)

    def test_feedback_link_used_flag(self):
        print("✓ test_feedback_link_used_flag: Field 'used' should be False by default and mutable")
        link = FeedbackLink.objects.create(service_order=self.order)
        self.assertFalse(link.used)
        link.used = True
        link.save()
        self.assertTrue(link.used)

    def test_feedback_link_created_at_auto(self):
        print("✓ test_feedback_link_created_at_auto: created_at should be filled in automatically")
        link = FeedbackLink.objects.create(service_order=self.order)
        self.assertIsNotNone(link.created_at)
