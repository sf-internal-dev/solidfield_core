# Public API v1 — contract and stability

This document describes the policy for the **Public v1 — Field operations** package documented in OpenAPI (`SPECTACULAR_SETTINGS.VERSION` = `1.0.0`).

## Where to view the schema

- **Swagger UI:** `GET /api/docs/` (Django server running).
- **OpenAPI JSON/YAML:** `GET /api/schema/` (format negotiated via the `Accept` header).

## Export the schema locally

From the repository root (`solidfield_core/`), with the project Python environment active:

```bash
python manage.py spectacular --file openapi.yaml
python manage.py spectacular --validate
```

## Versioning

- **Compatible** changes (new optional fields, additional documented error codes) may ship in `1.0.x`.
- **Incompatible** changes (removing fields, changing HTTP status-code semantics, renaming an `operation_id`) require a major version increment (for example `2.0.0`) and a client migration.

## Authentication

Public v1 endpoints follow the same authentication policy as the rest of the project's DRF API (for example JWT / session, as set in `REST_FRAMEWORK` in `backend/config/settings.py`). See the generated schema for the effective security schemes.

## Stable endpoints (Public v1 tags)

Routes are mounted under the **`/api/`** prefix as defined in `backend/apps/apis/urls.py`. Summary:

| Area | Route examples |
|------|----------------|
| Work orders | `create_work_order_api/`, `list_work_orders_api/`, `get_work_order_api/<id>/`, `update_work_order_api/<id>/`, `assign_work_order_api/<id>/`, `get_work_order_status_history_api/<id>/` |
| Checklist | routes in `checklist_api` (create, batch answers, listing, submit, progress, CSV export, and so on) |
| Offline sync | routes in `offline_sync_api` (enqueue, list, process) |

The stable operation names for client generators are the **`operation_id`** values in OpenAPI (prefix `publicV1…`).

## Documented common errors

- **422:** body with `codes` (a list of domain strings) and optionally `correlation_id` (UI message publishing).
- **400:** simple validation on some POST requests (for example a missing required field).

For exact per-route details, use the exported OpenAPI file or `/api/docs/`.
