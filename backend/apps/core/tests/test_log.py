from django.test import TestCase
from django.utils import timezone
from backend.apps.core.models import CompanyTenant, Technician, AuditLog

class AuditLogModelTest(TestCase):
    def setUp(self):
        print("→ setUp: Creating tenant and technician for audit tests...")
        self.tenant = CompanyTenant.objects.create(name="Tenant Logs", slug="tenant-logs")
        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="logtech",
            social_name="Log Technician",
            technician_permission="L1"
        )
        self.log_data = {
            "field": "status",
            "from": "open",
            "to": "in_progress"
        }

    def test_create_log_entry(self):
        print("✓ test_create_log_entry: Creating a basic audit entry")
        log = AuditLog.objects.create(
            tenant=self.tenant,
            technician=self.tech,
            action="status_update",
            reference_id="OS001",
            data=self.log_data
        )
        self.assertEqual(log.technician, self.tech)
        self.assertEqual(log.action, "status_update")
        self.assertEqual(log.reference_id, "OS001")
        self.assertEqual(log.data["to"], "in_progress")

    def test_created_at_auto(self):
        print("✓ test_created_at_auto: Field created_at should be filled in automatically")
        log = AuditLog.objects.create(
            tenant=self.tenant,
            technician=self.tech,
            action="photo_upload",
            reference_id="CHK001"
        )
        self.assertIsNotNone(log.created_at)
        self.assertLessEqual(log.created_at, timezone.now())

    def test_str_representation(self):
        print("✓ test_str_representation: __str__ should contain date, technician, and action")
        log = AuditLog.objects.create(
            tenant=self.tenant,
            technician=self.tech,
            action="checklist_edit",
            reference_id="CHK002"
        )
        str_repr = str(log)
        self.assertIn(str(log.created_at.date()), str_repr)
        self.assertIn("Log Technician", str_repr)
        self.assertIn("checklist_edit", str_repr)
        self.assertIn("CHK002", str_repr)

    def test_technician_can_be_null(self):
        print("✓ test_technician_can_be_null: Should allow a null technician in case of deletion")
        log = AuditLog.objects.create(
            tenant=self.tenant,
            technician=self.tech,
            action="delete_action",
            reference_id="GEN001"
        )
        self.tech.delete()
        log.refresh_from_db()
        self.assertIsNone(log.technician)
