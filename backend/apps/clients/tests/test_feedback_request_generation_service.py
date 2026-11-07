# backend/apps/clients/tests/test_feedback_request_generation_service.py

from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.db import IntegrityError
from django.utils import timezone

from backend.apps.core.models import CompanyTenant
from backend.apps.core.models.technician import Technician
from backend.apps.orders.models.work_order import WorkOrder
from backend.apps.clients.models.client import Client
from backend.apps.clients.models.feedback import FeedbackLink, ClientFeedback
from django.db import IntegrityError, transaction

from backend.apps.clients.services.feedback_request_generation_service import (
    create_feedback_link,
    return_feedback_preview,
    create_client_feedback,
)


class BaseSetupMixin(TestCase):
    def setUp(self):
        print("→ setUp: creating tenant, technician, and work order")
        self.tenant = CompanyTenant.objects.create(name="T1", slug="t1", tenant_code="T1AA")
        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="tech01",
            social_name="Tech One",
            technician_permission="L3",
            is_active=True,
        )

        now = timezone.now()

        
        self.client = Client.objects.create(
            tenant=self.tenant,
            person_type="company",
            name="Client Co",
            email="client@example.com",
            phone="+15555555555",
            document_id="123456789",
        )

        # Minimal WorkOrder (adjust fields if your model requires others)
        self.wo = WorkOrder.objects.create(
            tenant=self.tenant,            # TenantOwnedModel requires it
            identifier="WO-001",
            created_by=self.tech,
            assigned_to=self.tech,          # required
            work_start=now,                 # required
            work_end=now,                   # required (to simulate still open, it can stay = now)
            status="open",                  # required (any string valid in your domain)
            client=self.client,             # optional
            client_name=self.client.name,   # optional
            client_email=self.client.email, # optional
            client_phone=self.client.phone, # optional
            # first_access / has_remaining_work have defaults
            # status_history defaults to a list
        )


class CreateFeedbackLinkServiceTest(BaseSetupMixin):
    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(False, ["no_perm"]))
    def test_permission_denied(self, _perm):
        print("✓ create_feedback_link: no permission → None + ['no_perm']")
        link, errors = create_feedback_link(
            technician_operating=self.tech,
            work_order=self.wo,
        )
        self.assertIsNone(link)
        self.assertEqual(errors, ["no_perm"])

    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(True, []))
    @patch("backend.apps.clients.services.feedback_request_generation_service.generate_feedback_request_key", return_value="KEYOK")
    def test_success_first_try(self, _gen, _perm):
        print("✓ create_feedback_link: success on the 1st attempt")
        link, errors = create_feedback_link(
            technician_operating=self.tech,
            work_order=self.wo,
        )
        self.assertIsNotNone(link)
        self.assertEqual(errors, [])
        self.assertEqual(link.key, "KEYOK")
        self.assertEqual(link.work_order_id, self.wo.id)
        self.assertEqual(FeedbackLink.objects.count(), 1)

    from django.db import IntegrityError

    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(True, []))
    def test_retry_on_integrity_error_then_success(self, _perm):
        print("✓ create_feedback_link: 1st call raises IntegrityError (mock) → retry → success")
        call_count = {"n": 0}

        def create_side_effect(*args, **kwargs):
            if call_count["n"] == 0:
                call_count["n"] += 1
                raise IntegrityError("simulated duplicate key")
            # 2nd call: real creation
            return orig_create(*args, **kwargs)

        # switches the key from DUP1 to OK2 (only to cover the generation path)
        with patch(
            "backend.apps.clients.services.feedback_request_generation_service.generate_feedback_request_key",
            side_effect=["DUP1", "OK2"]
        ):
            # keep the real create and simulate an error only on the first call
            orig_create = FeedbackLink.objects.create
            with patch.object(FeedbackLink.objects, "create", side_effect=create_side_effect):
                link, errors = create_feedback_link(
                    technician_operating=self.tech,
                    work_order=self.wo,
                )
                self.assertIsNotNone(link)
                self.assertEqual(errors, [])
                self.assertEqual(link.key, "OK2")
                self.assertEqual(FeedbackLink.objects.count(), 1)

    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(True, []))
    def test_fails_after_five_collisions(self, _perm):
        print("✓ create_feedback_link: 5 collisions → 'key_generation_failed'")
        with patch(
            "backend.apps.clients.services.feedback_request_generation_service.generate_feedback_request_key",
            return_value="COLLIDE"
        ):
            # create one ahead of time with the same key to cause IntegrityError
            FeedbackLink.objects.create(work_order=self.wo, key="COLLIDE")

            # Monkeypatch create so it always raises IntegrityError
            orig_create = FeedbackLink.objects.create

            def always_integrity_error(*args, **kwargs):
                raise IntegrityError("duplicate key")

            with patch.object(FeedbackLink.objects, "create", side_effect=always_integrity_error):
                link, errors = create_feedback_link(
                    technician_operating=self.tech,
                    work_order=self.wo,
                )
                self.assertIsNone(link)
                self.assertIn("key_generation_failed", errors)


class ReturnFeedbackPreviewServiceTest(BaseSetupMixin):
    def test_return_feedback_preview_bug_passa_objeto_em_vez_de_str(self):
        print("✓ return_feedback_preview: documented BUG — passes an object to feedback_preview (expects str) → AttributeError")
        fb = ClientFeedback.objects.create(
            work_order=self.wo,
            client=self.client,
            client_name="Alice",
            client_email="alice@example.com",
            stars=5,
            strengths="speed",
        )
        # The current implementation does: feedback_preview(feedback)  # feedback is an object
        # feedback_preview expects a string and calls .strip(), raising AttributeError
        with self.assertRaises(AttributeError):
            return_feedback_preview(fb)


class CreateClientFeedbackServiceTest(BaseSetupMixin):
    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(False, ["no_perm"]))
    def test_permission_denied(self, _perm):
        print("✓ create_client_feedback: no permission → None + ['no_perm']")
        fb, errors = create_client_feedback(
            technician_operating=self.tech,
            work_order=self.wo,
            client=self.client,
            client_name="Alice",
            client_email="alice@example.com",
            stars=5,
            comment="great service",
            strengths="speed",
        )
        self.assertIsNone(fb)
        self.assertEqual(errors, ["no_perm"])

    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(True, []))
    def test_comment_too_long(self, _perm):
        print("✓ create_client_feedback: comment too long → 'comment_too_long'")
        long_comment = "x" * 151  # default limit = 150
        fb, errors = create_client_feedback(
            technician_operating=self.tech,
            work_order=self.wo,
            client=self.client,
            client_name="Alice",
            client_email="alice@example.com",
            stars=4,
            comment=long_comment,
            strengths="quality",
        )
        self.assertIsNone(fb)
        self.assertIn("comment_too_long", errors)
        self.assertEqual(ClientFeedback.objects.count(), 0)


    @patch("backend.apps.clients.services.feedback_request_generation_service.log_work_order_feedback_received")
    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(True, []))
    def test_success_with_client_documents_bug_doubles_insert_and_raises_integrity(self, _perm, _log):
        print("✓ create_client_feedback: WITH client → attempts 2 inserts → IntegrityError (documented bug)")
        # Isolates the exception in a savepoint; when the 2nd creation fails, EVERYTHING inside the savepoint is rolled back.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                _ = create_client_feedback(
                    technician_operating=self.tech,
                    work_order=self.wo,
                    client=self.client,
                    client_name="Alice",
                    client_email="alice+ignored@example.com",
                    stars=5,
                    comment="very good",
                    strengths="speed,quality",
                )

        # Because the error happened inside the same atomic block, the first creation was rolled back too.
        self.assertEqual(ClientFeedback.objects.filter(work_order=self.wo).count(), 0)

        # The log is called before the attempt to create the records; because it is outside the DB, it did run.
        _log.assert_called_once()

    @patch("backend.apps.clients.services.feedback_request_generation_service.log_work_order_feedback_received")
    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(True, []))
    def test_success_without_client_one_creation_and_return_type_bug(self, _perm, _log):
        print("✓ create_client_feedback: WITHOUT client → creates 1 record; return value is still only the object (BUG)")
        fb_return = create_client_feedback(
            technician_operating=self.tech,
            work_order=self.wo,
            client=None,
            client_name="Bob",
            client_email="bob@example.com",
            stars=4,
            comment="good",
            strengths="politeness",
        )
        self.assertIsInstance(fb_return, ClientFeedback)  # return value is not a tuple
        self.assertEqual(ClientFeedback.objects.count(), 1)
        rec = ClientFeedback.objects.first()
        self.assertIsNone(rec.client_id)
        self.assertEqual(rec.client_name, "Bob")
        self.assertEqual(rec.client_email, "bob@example.com")
        _log.assert_called_once()
