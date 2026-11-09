# Offline sync queue (`OfflineSyncQueue`)

For **device-only writes** that later call `enqueue` + `process`, see the client guide in **`CLIENT_OFFLINE_LOCAL_SYNC_SCHEMA.md`** (states, suggested SQLite/IndexedDB fields, diagram, and sync pseudo-code).

## Model

- `technician`: queue owner (normally the device technician).
- `status`: `pending` | `conflict` | `success`.
- `payload`: JSON with the mutation (see the contract below).
- `client_mutation_id`: optional, for **idempotency** (for example a UUID generated in the app); unique per technician when set.
- `synced_at`: set when the item is applied successfully.

Migration: `core.0004_offlinesyncqueue_client_mutation`.

## Permissions (schema)

- `enqueue_offline_sync` — enqueue items and list one's own queue.
- `process_offline_sync` — process pending items (or retry `conflict`).

Inherited at L1; L2 and L3 include these actions through selective inheritance in `permission_schemas`.

## APIs (`backend/apps/apis/urls.py`)

| Method | Path | Use |
|--------|------|-----|
| POST | `enqueue_offline_sync_api/` | Body: `payload` (object), optional `client_mutation_id`, optional `queue_owner_technician_id`. |
| GET | `list_offline_sync_api/` | Query: `status`, `limit`, `offset`. Lists only items for the authenticated technician. |
| POST | `process_offline_sync_api/<queue_id>/` | Applies one `pending` entry or reprocesses `conflict`. `success` is idempotent. |

## `payload` contract

```json
{
  "schema_version": 1,
  "action": "checklist_batch_answers",
  "body": {
    "checklist_id": 123,
    "answers": [
      { "item_template": 10, "value": 150.0, "note": "" }
    ]
  }
}
```

Another supported action:

- `checklist_submit` — `body`: `{ "checklist_id": 123 }` (equivalent to `submit_checklist` on the server).

New actions can be added in `core/services/offline_sync_service.py` (`process_offline_sync_item`).

## Recommended app flow

1. Offline: persist locally and, when possible, call `enqueue` with the same payload once the API is reachable, **or** keep the data local only and send a batch of `enqueue` calls on reconnect.
2. Online: call `process_offline_sync_api` for each pending `queue_id` (or in series).
3. Always use a `client_mutation_id` (UUID) per mutation so repeated submits do not duplicate answers.

## Service

Implementation: `backend/apps/core/services/offline_sync_service.py`.
