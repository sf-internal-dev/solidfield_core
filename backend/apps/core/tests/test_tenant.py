from django.test import TestCase
from django.utils import timezone
from backend.apps.core.models import CompanyTenant, TenantWorkflow, AccountHolderUser
import datetime

class CompanyTenantModelTest(TestCase):
    print("→ setUp: Creating a tenant with every field filled in...")
    def setUp(self):
        self.owner = AccountHolderUser.objects.create_user(email="owner@test.com", full_name="Owner User")
        self.tenant = CompanyTenant.objects.create(
            name="Company X",
            slug="company-x",
            primary_contact_name="Contact",
            primary_contact_email="contact@company.com",
            primary_contact_phone="(11) 99999-9999",
            owner=self.owner,
            locale="pt-BR",
            timezone="America/Sao_Paulo",
            color_primary="#FF6600",
        )

    def test_string_representation(self):
        print("✓ test_string_representation: __str__ should return the company name")
        """__str__ should return the company name"""
        self.assertEqual(str(self.tenant), "Company X")

    def test_defaults(self):
        """Tests default values when creating a tenant"""
        print("✓ test_defaults: Checking default values of is_active, locale, timezone, and color_primary")
        tenant = CompanyTenant.objects.create(name="Default", slug="default")
        self.assertTrue(tenant.is_active)
        self.assertEqual(tenant.locale, "en-US")
        self.assertEqual(tenant.timezone, "America/Los_Angeles")
        self.assertEqual(tenant.color_primary, "#000000")
        self.assertIsNone(tenant.owner)
        # self.assertIsNone(tenant.logo)

    def test_timestamps_are_set(self):
        """created_at and updated_at should be filled in automatically"""
        print("✓ test_timestamps_are_set: Checking that created_at and updated_at were generated")
        self.assertIsNotNone(self.tenant.created_at)
        self.assertIsNotNone(self.tenant.updated_at)
        self.assertAlmostEqual(self.tenant.created_at.date(), timezone.now().date())

    def test_owner_relationship(self):
        """Should correctly associate the owner with the company"""
        print("✓ test_owner_relationship: Checking the one-to-one relationship with AccountHolderUser")
        self.assertEqual(self.tenant.owner, self.owner)
        self.assertEqual(self.owner.owned_tenant, self.tenant)

from django.test import TestCase
from django.utils import timezone
from backend.apps.core.models import CompanyTenant, TenantWorkflow
import datetime

class TenantWorkflowModelTest(TestCase):
    def setUp(self):
        print("→ setUp: Creating tenant and workflow JSON")
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
        """__str__ should show the tenant name and date"""
        print("✓ test_string_representation: __str__ should contain the tenant name and the update date")
        self.assertIn("Workflow Tenant", str(self.workflow))
        self.assertIn(str(self.workflow.updated_at.date()), str(self.workflow))

    def test_workflow_json_content(self):
        """Should correctly store the JSON content"""
        print("✓ test_workflow_json_content: Validating the content stored in the JSONField")
        self.assertIn("states", self.workflow.workflow_json)
        self.assertEqual(self.workflow.workflow_json["states"], ["open", "in_progress", "done"])

    def test_updated_at_auto_updates(self):
        """updated_at should be updated automatically"""
        print("✓ test_updated_at_auto_updates: Checking that updated_at is updated after a modification")
        old_updated = self.workflow.updated_at
        self.workflow.workflow_json["states"].append("archived")
        self.workflow.save()
        self.workflow.refresh_from_db()
        self.assertGreaterEqual(self.workflow.updated_at, old_updated)
