from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from backend.apps.core.models import CompanyTenant, Technician, OfflineSyncQueue

class OfflineSyncQueueModelTest(TestCase):
    def setUp(self):
        print("→ setUp: Creating tenant and technician for the offline sync queue...")
        self.tenant = CompanyTenant.objects.create(name="Tenant Sync", slug="tenant-sync")
        self.technician = Technician.objects.create(
            tenant=self.tenant,
            username="sync_tech",
            social_name="Sync Tech",
            technician_permission="L1"
        )
        self.payload_data = {
            "model": "checklist",
            "data": {"id": 1, "answer": True}
        }

    def test_create_pending_sync_entry(self):
        print("✓ test_create_pending_sync_entry: Creating a sync item with status 'pending'")
        sync_entry = OfflineSyncQueue.objects.create(
            technician=self.technician,
            status="pending",
            payload=self.payload_data
        )
        self.assertEqual(sync_entry.status, "pending")
        self.assertEqual(sync_entry.payload, self.payload_data)
        self.assertIsNone(sync_entry.synced_at)

    def test_default_created_at(self):
        print("✓ test_default_created_at: created_at should be filled in automatically")
        sync_entry = OfflineSyncQueue.objects.create(
            technician=self.technician,
            status="pending",
            payload=self.payload_data
        )
        now = timezone.now()
        self.assertLessEqual(sync_entry.created_at, now)

    def test_str_representation(self):
        print("✓ test_str_representation: __str__ should contain technician, status, and formatted date")
        sync_entry = OfflineSyncQueue.objects.create(
            technician=self.technician,
            status="success",
            payload=self.payload_data
        )
        str_repr = str(sync_entry)
        self.assertIn("Sync Tech", str_repr)
        self.assertIn("success", str_repr)
        self.assertIn(str(sync_entry.created_at.strftime("%Y-%m-%d %H:%M")), str_repr)

    def test_conflict_status(self):
        print("✓ test_conflict_status: Should allow saving status 'conflict'")
        sync_entry = OfflineSyncQueue.objects.create(
            technician=self.technician,
            status="conflict",
            payload=self.payload_data
        )
        self.assertEqual(sync_entry.status, "conflict")

    def test_synced_at_can_be_set(self):
        print("✓ test_synced_at_can_be_set: Should allow setting 'synced_at' manually")
        timestamp = timezone.now() - timedelta(minutes=5)
        sync_entry = OfflineSyncQueue.objects.create(
            technician=self.technician,
            status="success",
            payload=self.payload_data,
            synced_at=timestamp
        )
        self.assertEqual(sync_entry.synced_at, timestamp)
