"""
Serviço da fila offline: enfileirar mutações no dispositivo e processar quando há conectividade.

Contrato de `payload` (mínimo):
- `schema_version`: int (ex.: 1)
- `action`: str
- `body`: dict específico da ação

Ações suportadas:
- `checklist_batch_answers` — body: `checklist_id`, `answers` (lista compatível com bulk_save_answers)
- `checklist_submit` — body: `checklist_id`
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from django.db import IntegrityError, transaction
from django.utils import timezone

from backend.apps.checklist.models import Checklist
from backend.apps.checklist.services.checklist_service import bulk_save_answers, submit_checklist
from backend.apps.core.models.sync import OfflineSyncQueue
from backend.apps.core.models.technician import Technician
from backend.apps.core.services.technician_permission_service import has_permission


def _permission_errors(technician: Technician, action_code: str) -> List[str]:
    ok, msg = has_permission(technician, action_code)
    if ok:
        return []
    if msg:
        return [msg]
    return ["permission_denied"]


def enqueue_offline_sync_item(
    *,
    technician_operating: Technician,
    payload: Dict[str, Any],
    client_mutation_id: Optional[str] = None,
    queue_owner: Optional[Technician] = None,
) -> Tuple[Optional[OfflineSyncQueue], List[str]]:
    errors = _permission_errors(technician_operating, "enqueue_offline_sync")
    if errors:
        return None, errors

    if not isinstance(payload, dict):
        return None, ["invalid_payload"]

    mid = (client_mutation_id or "").strip() or None
    owner = queue_owner or technician_operating
    if owner.tenant_id != technician_operating.tenant_id:
        return None, ["queue_owner_tenant_mismatch"]

    if mid:
        existing = (
            OfflineSyncQueue.objects.filter(technician=owner, client_mutation_id=mid)
            .order_by("-id")
            .first()
        )
        if existing:
            if existing.status == "success":
                return existing, []
            if existing.status == "pending":
                return existing, []
            if existing.status == "conflict":
                return existing, ["conflict_retry_use_process"]

    try:
        row = OfflineSyncQueue.objects.create(
            technician=owner,
            status="pending",
            payload=payload,
            client_mutation_id=mid,
        )
        return row, []
    except IntegrityError:
        dup = OfflineSyncQueue.objects.filter(technician=owner, client_mutation_id=mid).first()
        if dup:
            return dup, []
        return None, ["enqueue_integrity_error"]


def list_my_offline_sync_queue(
    *,
    technician_operating: Technician,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[OfflineSyncQueue], List[str]]:
    errors = _permission_errors(technician_operating, "enqueue_offline_sync")
    if errors:
        return [], errors

    qs = OfflineSyncQueue.objects.filter(
        technician_id=technician_operating.id,
        technician__tenant_id=technician_operating.tenant_id,
    ).order_by("-created_at")
    if status:
        qs = qs.filter(status=status)
    return list(qs[offset : offset + limit]), []


def process_offline_sync_item(
    *,
    technician_operating: Technician,
    queue_id: int,
) -> Tuple[Optional[str], List[str]]:
    errors = _permission_errors(technician_operating, "process_offline_sync")
    if errors:
        return None, errors

    try:
        with transaction.atomic():
            row = OfflineSyncQueue.objects.select_for_update().get(
                id=queue_id,
                technician_id=technician_operating.id,
                technician__tenant_id=technician_operating.tenant_id,
            )
            if row.status == "success":
                return "success", []
            if row.status not in ("pending", "conflict"):
                return row.status, ["cannot_process_status"]
            row.status = "pending"
            row.save(update_fields=["status", "updated_at"])

            action = (row.payload or {}).get("action")
            body = (row.payload or {}).get("body") or {}

            if action == "checklist_batch_answers":
                checklist_id = body.get("checklist_id")
                if not checklist_id:
                    row.status = "conflict"
                    row.payload = {**row.payload, "sync_error_codes": ["checklist_id_required"]}
                    row.save(update_fields=["status", "payload", "updated_at"])
                    return "conflict", ["checklist_id_required"]
                try:
                    checklist = Checklist.objects.get(
                        id=checklist_id,
                        template__tenant_id=technician_operating.tenant_id,
                    )
                except Checklist.DoesNotExist:
                    row.status = "conflict"
                    row.payload = {**row.payload, "sync_error_codes": ["checklist_not_found"]}
                    row.save(update_fields=["status", "payload", "updated_at"])
                    return "conflict", ["checklist_not_found"]

                payloads = body.get("answers") or []
                if not isinstance(payloads, list):
                    row.status = "conflict"
                    row.payload = {**row.payload, "sync_error_codes": ["answers_must_be_list"]}
                    row.save(update_fields=["status", "payload", "updated_at"])
                    return "conflict", ["answers_must_be_list"]

                _, ans_errs = bulk_save_answers(
                    technician_operating=technician_operating,
                    checklist=checklist,
                    payloads=payloads,
                )
                if ans_errs:
                    row.status = "conflict"
                    row.payload = {**row.payload, "sync_error_codes": ans_errs}
                    row.save(update_fields=["status", "payload", "updated_at"])
                    return "conflict", ans_errs

                row.status = "success"
                row.synced_at = timezone.now()
                row.save(update_fields=["status", "synced_at", "updated_at"])
                return "success", []

            if action == "checklist_submit":
                checklist_id = body.get("checklist_id")
                if not checklist_id:
                    row.status = "conflict"
                    row.payload = {**row.payload, "sync_error_codes": ["checklist_id_required"]}
                    row.save(update_fields=["status", "payload", "updated_at"])
                    return "conflict", ["checklist_id_required"]
                ok_submit, sub_errs = submit_checklist(
                    technician_operating=technician_operating,
                    checklist_id=int(checklist_id),
                )
                if not ok_submit:
                    row.status = "conflict"
                    row.payload = {**row.payload, "sync_error_codes": sub_errs}
                    row.save(update_fields=["status", "payload", "updated_at"])
                    return "conflict", sub_errs
                row.status = "success"
                row.synced_at = timezone.now()
                row.save(update_fields=["status", "synced_at", "updated_at"])
                return "success", []

            row.status = "conflict"
            row.payload = {
                **row.payload,
                "sync_error_codes": [f"unknown_action:{action}"],
            }
            row.save(update_fields=["status", "payload", "updated_at"])
            return "conflict", [f"unknown_action:{action}"]

    except OfflineSyncQueue.DoesNotExist:
        return None, ["queue_item_not_found"]
