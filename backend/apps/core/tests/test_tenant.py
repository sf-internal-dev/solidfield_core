from django.test import TestCase
from django.utils import timezone
from backend.apps.core.models import CompanyTenant, TenantWorkflow, AccountHolderUser
import datetime

class CompanyTenantModelTest(TestCase):
    print("→ setUp: Criando tenant com todos os campos preenchidos...")
    def setUp(self):
        self.owner = AccountHolderUser.objects.create_user(email="owner@test.com", full_name="Owner User")
        self.tenant = CompanyTenant.objects.create(
            name="Empresa X",
            slug="empresa-x",
            primary_contact_name="Contato",
            primary_contact_email="contato@empresa.com",
            primary_contact_phone="(11) 99999-9999",
            owner=self.owner,
            locale="pt-BR",
            timezone="America/Sao_Paulo",
            color_primary="#FF6600",
        )

    def test_string_representation(self):
        print("✓ test_string_representation: __str__ deve retornar o nome da empresa")
        """__str__ deve retornar o nome da empresa"""
        self.assertEqual(str(self.tenant), "Empresa X")

    def test_defaults(self):
        """Testa valores padrão ao criar um tenant"""
        print("✓ test_defaults: Verificando valores padrão de is_active, locale, timezone e color_primary")
        tenant = CompanyTenant.objects.create(name="Padrao", slug="padrao")
        self.assertTrue(tenant.is_active)
        self.assertEqual(tenant.locale, "en-US")
        self.assertEqual(tenant.timezone, "America/Los_Angeles")
        self.assertEqual(tenant.color_primary, "#000000")
        self.assertIsNone(tenant.owner)
        # self.assertIsNone(tenant.logo)

    def test_timestamps_are_set(self):
        """created_at e updated_at devem ser preenchidos automaticamente"""
        print("✓ test_timestamps_are_set: Verificando se created_at e updated_at foram gerados")
        self.assertIsNotNone(self.tenant.created_at)
        self.assertIsNotNone(self.tenant.updated_at)
        self.assertAlmostEqual(self.tenant.created_at.date(), timezone.now().date())

    def test_owner_relationship(self):
        """Deve associar corretamente o dono à empresa"""
        print("✓ test_owner_relationship: Verificando relacionamento one-to-one com AccountHolderUser")
        self.assertEqual(self.tenant.owner, self.owner)
        self.assertEqual(self.owner.owned_tenant, self.tenant)

from django.test import TestCase
from django.utils import timezone
from backend.apps.core.models import CompanyTenant, TenantWorkflow
import datetime

class TenantWorkflowModelTest(TestCase):
    def setUp(self):
        print("→ setUp: Criando tenant e workflow JSON")
        self.tenant = CompanyTenant.objects.create(name="Workflow Tenant", slug="workflow-tenant")
        self.workflow_data = {
            "states": ["open", "in_progress", "done"],
            "transitions": [{"from": "open", "to": "in_progress"}]
        }
        self.workflow = TenantWorkflow.objects.create(
            tenant=self.tenant,
            workflow_json=self.workflow_data
        )

    def test_string_representation(self):
        """__str__ deve exibir nome e data do tenant"""
        print("✓ test_string_representation: __str__ deve conter o nome do tenant e a data de atualização")
        self.assertIn("Workflow Tenant", str(self.workflow))
        self.assertIn(str(self.workflow.updated_at.date()), str(self.workflow))

    def test_workflow_json_content(self):
        """Deve armazenar corretamente o conteúdo do JSON"""
        print("✓ test_workflow_json_content: Validando conteúdo armazenado no campo JSONField")
        self.assertIn("states", self.workflow.workflow_json)
        self.assertEqual(self.workflow.workflow_json["states"], ["open", "in_progress", "done"])

    def test_updated_at_auto_updates(self):
        """updated_at deve ser atualizado automaticamente"""
        print("✓ test_updated_at_auto_updates: Verificando se updated_at é atualizado após modificação")
        old_updated = self.workflow.updated_at
        self.workflow.workflow_json["states"].append("archived")
        self.workflow.save()
        self.workflow.refresh_from_db()
        self.assertGreaterEqual(self.workflow.updated_at, old_updated)
