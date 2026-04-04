from unittest.mock import patch

from django.test import TestCase

from backend.apps.core.models import CompanyTenant, Technician
from backend.apps.core.models.sync import OfflineSyncQueue
from backend.apps.core.services import offline_sync_service as svc


class OfflineSyncServiceTestCase(TestCase):
    def setUp(self):
        self.tenant = CompanyTenant.objects.create(name="T OS", slug="t-os")
        self.tech = Technician.objects.create(
            tenant=self.tenant,
            username="tos",
            social_name="Tech OS",
            technician_permission="L1",
        )

    @patch(
        "backend.apps.core.services.offline_sync_service.has_permission",
        return_value=(True, ""),
    )
    def test_enqueue_and_idempotent_mutation_id(self, _mock_perm):
        payload = {"schema_version": 1, "action": "checklist_batch_answers", "body": {}}
        row1, err1 = svc.enqueue_offline_sync_item(
            technician_operating=self.tech,
            payload=payload,
            client_mutation_id="abc-123",
        )
        self.assertEqual(err1, [])
        self.assertEqual(row1.status, "pending")

        row2, err2 = svc.enqueue_offline_sync_item(
            technician_operating=self.tech,
            payload=payload,
            client_mutation_id="abc-123",
        )
        self.assertEqual(err2, [])
        self.assertEqual(row1.id, row2.id)
        self.assertEqual(OfflineSyncQueue.objects.filter(client_mutation_id="abc-123").count(), 1)

    @patch(
        "backend.apps.core.services.offline_sync_service.has_permission",
        return_value=(True, ""),
    )
    def test_list_my_queue(self, _mock_perm):
        OfflineSyncQueue.objects.create(
            technician=self.tech,
            status="pending",
            payload={"action": "x"},
        )
        rows, errs = svc.list_my_offline_sync_queue(technician_operating=self.tech)
        self.assertEqual(errs, [])
        self.assertEqual(len(rows), 1)

    @patch(
        "backend.apps.core.services.offline_sync_service.submit_checklist",
        return_value=(True, []),
    )
    @patch(
        "backend.apps.core.services.offline_sync_service.has_permission",
        return_value=(True, ""),
    )
    def test_process_checklist_submit_success(self, _mock_perm, _mock_submit):
        row = OfflineSyncQueue.objects.create(
            technician=self.tech,
            status="pending",
            payload={"action": "checklist_submit", "body": {"checklist_id": 42}},
        )
        final, errs = svc.process_offline_sync_item(
            technician_operating=self.tech,
            queue_id=row.id,
        )
        self.assertEqual(final, "success")
        self.assertEqual(errs, [])
        row.refresh_from_db()
        self.assertEqual(row.status, "success")
        self.assertIsNotNone(row.synced_at)
