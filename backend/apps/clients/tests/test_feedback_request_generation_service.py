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
        print("→ setUp: criando tenant, técnico e ordem de serviço")
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

        # WorkOrder mínimo (ajuste campos se o seu modelo exigir outros)
        self.wo = WorkOrder.objects.create(
            tenant=self.tenant,            # TenantOwnedModel exige
            identifier="WO-001",
            created_by=self.tech,
            assigned_to=self.tech,          # obrigatório
            work_start=now,                 # obrigatório
            work_end=now,                   # obrigatório (se quiser simular em aberto, pode pôr = now)
            status="open",                  # obrigatório (qualquer string válida no seu domínio)
            client=self.client,             # opcional
            client_name=self.client.name,   # opcional
            client_email=self.client.email, # opcional
            client_phone=self.client.phone, # opcional
            # first_access / has_remaining_work têm default
            # status_history tem default list
        )


class CreateFeedbackLinkServiceTest(BaseSetupMixin):
    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(False, ["no_perm"]))
    def test_permission_denied(self, _perm):
        print("✓ create_feedback_link: sem permissão → None + ['no_perm']")
        link, errors = create_feedback_link(
            technician_operating=self.tech,
            work_order=self.wo,
        )
        self.assertIsNone(link)
        self.assertEqual(errors, ["no_perm"])

    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(True, []))
    @patch("backend.apps.clients.services.feedback_request_generation_service.generate_feedback_request_key", return_value="KEYOK")
    def test_success_first_try(self, _gen, _perm):
        print("✓ create_feedback_link: sucesso na 1ª tentativa")
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
        print("✓ create_feedback_link: 1ª chamada levanta IntegrityError (mock) → retry → sucesso")
        call_count = {"n": 0}

        def create_side_effect(*args, **kwargs):
            if call_count["n"] == 0:
                call_count["n"] += 1
                raise IntegrityError("simulated duplicate key")
            # 2ª chamada: criação real
            return orig_create(*args, **kwargs)

        # alterna a key de DUP1 para OK2 (apenas para cobrir o caminho de geração)
        with patch(
            "backend.apps.clients.services.feedback_request_generation_service.generate_feedback_request_key",
            side_effect=["DUP1", "OK2"]
        ):
            # guardamos o create real e simulamos erro só na primeira
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
        print("✓ create_feedback_link: 5 colisões → 'key_generation_failed'")
        with patch(
            "backend.apps.clients.services.feedback_request_generation_service.generate_feedback_request_key",
            return_value="COLLIDE"
        ):
            # cria previamente com a mesma key para causar IntegrityError
            FeedbackLink.objects.create(work_order=self.wo, key="COLLIDE")

            # Monkeypatchar o create para levantar IntegrityError sempre
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
        print("✓ return_feedback_preview: BUG documentado — passa objeto para feedback_preview (espera str) → AttributeError")
        fb = ClientFeedback.objects.create(
            work_order=self.wo,
            client=self.client,
            client_name="Alice",
            client_email="alice@example.com",
            stars=5,
            strengths="speed",
        )
        # A implementação atual faz: feedback_preview(feedback)  # feedback é objeto
        # feedback_preview espera uma string e chama .strip(), gerando AttributeError
        with self.assertRaises(AttributeError):
            return_feedback_preview(fb)


class CreateClientFeedbackServiceTest(BaseSetupMixin):
    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(False, ["no_perm"]))
    def test_permission_denied(self, _perm):
        print("✓ create_client_feedback: sem permissão → None + ['no_perm']")
        fb, errors = create_client_feedback(
            technician_operating=self.tech,
            work_order=self.wo,
            client=self.client,
            client_name="Alice",
            client_email="alice@example.com",
            stars=5,
            comment="ótimo atendimento",
            strengths="speed",
        )
        self.assertIsNone(fb)
        self.assertEqual(errors, ["no_perm"])

    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(True, []))
    def test_comment_too_long(self, _perm):
        print("✓ create_client_feedback: comentário longo demais → 'comment_too_long'")
        long_comment = "x" * 151  # limite padrão = 150
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
        print("✓ create_client_feedback: COM client → tentativa de 2 inserts → IntegrityError (bug documentado)")
        # Isola a exceção num savepoint; quando a 2ª criação falha, TUDO dentro do savepoint é revertido.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                _ = create_client_feedback(
                    technician_operating=self.tech,
                    work_order=self.wo,
                    client=self.client,
                    client_name="Alice",
                    client_email="alice+ignored@example.com",
                    stars=5,
                    comment="muito bom",
                    strengths="speed,quality",
                )

        # Como o erro ocorreu dentro do mesmo atomic, a primeira criação também foi revertida.
        self.assertEqual(ClientFeedback.objects.filter(work_order=self.wo).count(), 0)

        # O log é chamado antes da tentativa de criar os registros; como está fora do DB, ele ocorreu.
        _log.assert_called_once()

    @patch("backend.apps.clients.services.feedback_request_generation_service.log_work_order_feedback_received")
    @patch("backend.apps.clients.services.feedback_request_generation_service.has_permission", return_value=(True, []))
    def test_success_without_client_one_creation_and_return_type_bug(self, _perm, _log):
        print("✓ create_client_feedback: SEM client → cria 1 registro; retorno ainda é só objeto (BUG)")
        fb_return = create_client_feedback(
            technician_operating=self.tech,
            work_order=self.wo,
            client=None,
            client_name="Bob",
            client_email="bob@example.com",
            stars=4,
            comment="bom",
            strengths="politeness",
        )
        self.assertIsInstance(fb_return, ClientFeedback)  # retorno não é tuple
        self.assertEqual(ClientFeedback.objects.count(), 1)
        rec = ClientFeedback.objects.first()
        self.assertIsNone(rec.client_id)
        self.assertEqual(rec.client_name, "Bob")
        self.assertEqual(rec.client_email, "bob@example.com")
        _log.assert_called_once()
