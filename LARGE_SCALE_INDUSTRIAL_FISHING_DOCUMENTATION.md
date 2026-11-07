# Documentation — Transforming SolidField for Large-Scale Industrial Fishing

This document consolidates **what already exists in the repository**, **what is in progress**, and **the product line** for a system aimed at **shipowners / industrial fleets** (a hub scenario such as Itajaí/SC), reusing the existing Django backend with **minimal web-UI dependency** in the MVP (APIs + export + a client app when one exists).

---

## 1. Goal of the transformation

Turn SolidField from a **generic field-operations SaaS** into a **lean package** focused on the **operational daily log at sea**:

- **Diesel** (consumption, refueling, on-board estimate)
- **Ice** (estimated mass)
- **Cold-room / hold temperature**
- **Shift / period** and **notes** in the operational scope

With an **explicit link to the voyage** (`WorkOrder` as the logical container), **fill and submission state**, **offline sync** when there is no network, and **tabular output** for BI (Excel, Sheets, Power BI).

That attacks **immediate OPEX** (fuel, perishables) and prepares the ground for an **official vessel log (Mapa de Bordo)** and regulatory reports in a later phase — without confusing the MVP with the **catch share** (a corporate engine that **does not exist** in the code yet).

---

## 2. Architecture view (MVP)

```
┌─────────────────┐     HTTPS (when the network is up)     ┌──────────────────────────┐
│  Field app      │ ──────────────────────────────────► │  Django / DRF (SolidField)│
│  (Capacitor+    │   checklist, work orders, sync queue │  multi-tenant, RBAC       │
│   Vue+Ionic)*   │ ◄────────────────────────────────── │                           │
└────────┬────────┘                                     └────────────┬─────────────┘
         │                                                          │
         │ local SQLite/IndexedDB                                   │ Postgres
         │ (queued mutations)                                       │ WorkOrder, Checklist,
         └──────────────────────────────────────────────────────────► OfflineSyncQueue, …
```

\* **A dedicated frontend is not in this repository yet**; the sync guidance and contract are documented under `backend/apps/core/` (see section 7).

Role of the backend in this MVP:

- **Source of truth** after sync
- **Mutation queue** (`OfflineSyncQueue`) to apply an answer batch and an idempotent submit
- **CSV export** aggregating answers by voyage / service type

---

## 3. What already exists (implemented)

### 3.1 Checklist domain + industrial-fishing template

| Delivery | Description | Where |
|----------|-------------|-------|
| Versioned template v1 | 7 items: shift (text), diesel (L × 3), ice (kg), temperature (°C), notes | `backend/apps/checklist/defaults/pesca_diario_operacional.py` |
| Product constants | Name: `Daily Operational Log — Industrial Fishing`; `service_type`: `pesca_industrial_diario` | Same file |
| Idempotent seed | Django command per tenant / technician | `backend/apps/checklist/management/commands/seed_pesca_diario_operacional.py` |
| Numeric types | `volume_l`, `weight_kg`, `temperature` aligned with shared codecs | `backend.common.number_codecs` (referenced from defaults) |

Supporting documentation:

- `backend/apps/checklist/CHECKLIST_SCHEMA.md` — entities, flows, invariants, APIs
- `backend/apps/checklist/CHECKLIST_NUMERIC_FORMS_AND_FISHING.md` — versioned forms and the link to the codecs

### 3.2 Checklist ↔ voyage (`WorkOrder`)

- Checklist creation with optional **`work_order`** and optional **`filled_by`**
- Aligned **tenant** validation (template, work order, technician)
- Service and API updated (`checklist_service.py`, `checklist_api.py`)

### 3.3 Lifecycle and progress

- **`Checklist.status`** field: `draft` | `submitted` (migration `0004_checklist_status`)
- **`submit_checklist`** sets `submitted` and **`incomplete=False`** when applicable
- Serializers expose **`status`** and **`incomplete`**
- APIs: progress, listing, detail, answer removal (see URLs)

### 3.4 Batch answers

- Endpoint **`POST .../create_checklist_item_answer_api/`** uses **`bulk_save_answers`** with `technician_operating` (permission fix applied in the service)

### 3.5 Export for analysis (BI / Excel)

- **`GET .../export_checklist_answers_csv_api/`** with optional filters: `work_order_id`, `service_type` (for example `pesca_industrial_diario`), `template_id`
- UTF-8 **with BOM** for Excel
- Implementation: `backend/apps/checklist/services/checklist_export_service.py`

### 3.6 Offline queue

| Delivery | Description | Where |
|----------|-------------|-------|
| Model | `OfflineSyncQueue` with `pending` / `conflict` / `success`, JSON `payload` | `backend/apps/core/models/sync.py` |
| Idempotency | `client_mutation_id` unique per technician (when set) | Migration `core.0004_offlinesyncqueue_client_mutation` |
| Service | Enqueue, list, process with a lock; actions `checklist_batch_answers`, `checklist_submit` | `backend/apps/core/services/offline_sync_service.py` |
| APIs | `enqueue_offline_sync_api/`, `list_offline_sync_api/`, `process_offline_sync_api/<queue_id>/` | `backend/apps/core/api/offline_sync_api.py` + `apis/urls.py` |
| Permissions | `enqueue_offline_sync`, `process_offline_sync` | `backend/common/schemas/permission_schemas.py` |
| Tests | Offline service | `backend/apps/core/tests/test_offline_sync_service.py` |

Documentation: `backend/apps/core/OFFLINE_SYNC_QUEUE.md`, `CLIENT_OFFLINE_LOCAL_SYNC_SCHEMA.md`, `CAPACITOR_VUE_IONIC_OFFLINE_SYNC.md`

### 3.7 Work orders (voyage / work order)

APIs registered in `backend/apps/apis/urls.py`: create, list, get, update, assign, status history, download link (the last one follows the legacy SolidField product).

### 3.8 Public API contract (OpenAPI)

- **Swagger UI:** `GET /api/docs/`
- **Schema:** `GET /api/schema/`
- Configuration: `backend/config/urls.py`, `drf_spectacular`, `SPECTACULAR_SETTINGS` in `backend/config/settings.py`
- Stable tags and `operation_id` values (prefix `publicV1…`) for checklist, work orders, offline sync
- Documented policy: `API_PUBLIC_CONTRACT.md`

### 3.9 Other reusable SolidField assets (not fishing-exclusive)

- **`filehub`:** photos / signatures with geo — useful as evidence of a gauge or cold room (**per-item integration is not closed in the fishing flow yet**)
- **`reporting`:** base for PDF/reports — the **official regulatory layout** is not treated as done in the MVP
- **RBAC / multi-tenant / audit:** `core` — they carry the vertical product

Macro view of the engines: `MICROSAAS_HEADLESS_AUDIT.md`

---

## 4. Main HTTP routes (prefix `/api/`)

Central definition: `backend/apps/apis/urls.py`.

**Offline sync**

- `POST enqueue_offline_sync_api/`
- `GET list_offline_sync_api/`
- `POST process_offline_sync_api/<int:queue_id>/`

**Checklist (fishing MVP)**

- `POST create_checklist_api/` — body: `template`, optional `work_order`, `filled_by`
- `POST create_checklist_item_answer_api/` — batch answers
- `DELETE remove_checklist_answer_api/<checklist_id>/<item_template_id>/`
- `GET list_checklists_api/`
- `GET get_checklist_api/<checklist_id>/`
- `POST submit_checklist_api/<checklist_id>/`
- `GET get_checklist_progress_api/<checklist_id>/`
- `GET export_checklist_answers_csv_api/`

**Templates** (tenant administration / configuration)

- `create_checklist_template_api/`, `create_checklist_item_template_api/`, delegation to groups, template version, and so on.

**Work orders**

- `create_work_order_api/`, `list_work_orders_api/`, `get_work_order_api/<id>/`, `update_work_order_api/<id>/`, `assign_work_order_api/<id>/`, `get_work_order_status_history_api/<id>/`, `create_work_order_download_link_api/`

Authentication and error format follow the project’s DRF pattern (see `API_PUBLIC_CONTRACT.md` and the OpenAPI schema).

---

## 5. Recommended operational order (backend)

1. `python manage.py migrate`
2. `python manage.py seed_pesca_diario_operacional --tenant-id <id> --technician-id <id>` (or the equivalent without flags, per the command doc)
3. Create/use a **`WorkOrder`** in the same tenant
4. `POST /api/create_checklist_api/` with `template` + `work_order`
5. Save answers: **directly** via `create_checklist_item_answer_api` or **offline** via `enqueue_offline_sync_api` + `process_offline_sync_api`
6. `POST /api/submit_checklist_api/<id>/` when the daily log is complete
7. `GET /api/export_checklist_answers_csv_api/?service_type=pesca_industrial_diario&work_order_id=...` for external analysis

Details and change history: `FISHING_CHECKLIST_IMPLEMENTATION_HISTORY.md`

---

## 6. Product strategy (Itajaí / industrial context)

Reference document: `MICROSAAS_INDUSTRIAL_FISHING_ITAJAI.md`

Summary:

- **MVP priority:** diesel + ice + temperature (direct cash impact)
- **Official vessel log:** the same checklist engine + audit; legal/PDF layer in a later phase
- **Catch share:** outside the current core; it needs a new domain (catch, price, corporate rules)

---

## 7. What we are working on / next increments

These items are **explicit planning** or **gaps** recognized in the code/docs:

| Area | State |
|------|-------|
| Freeze and publish the HTTP contract (`operation_id`, 422 errors) | In progress / partly covered by OpenAPI Public v1 |
| Capacitor + Vue + Ionic app (UI + local storage + sync) | **Not in this repo**; design documentation in `CAPACITOR_VUE_IONIC_OFFLINE_SYNC.md` and `CLIENT_OFFLINE_LOCAL_SYNC_SCHEMA.md` |
| Photographic evidence per item (gauge/cold room) via `filehub` | **Not integrated** end to end with the fishing daily-log flow |
| Official vessel log under specific rules (PDF/validation with the authority) | **Not implemented** as a regulatory product |
| Catch-share engine | **Absent** from the repository |
| Dashboard or scheduled reports | The MVP assumes **CSV + external consumers** |
| Automatic telemetry (CAN, sensors) | **Out of scope** for the current checklist |

---

## 8. Limitations and compliance

- **Fishing, safety, and mandatory-documentation** rules must be validated with **specialists and the competent authorities**. This software provides **structured recording and technical traceability**; it does not replace legal advice or official-format approval.
- The repository does not yet include a **production SPA** for the vertical; the implemented focus is **API + data + sync**.

---

## 9. Index of related documentation

| Document | Contents |
|----------|----------|
| `MICROSAAS_INDUSTRIAL_FISHING_ITAJAI.md` | Strategy, sector pains, 30-day MVP, fit with the modules |
| `FISHING_CHECKLIST_IMPLEMENTATION_HISTORY.md` | Technical chronology of what was implemented and fixed |
| `MICROSAAS_HEADLESS_AUDIT.md` | Inventory of reusable engines (work orders, RBAC, sync, checklist) |
| `API_PUBLIC_CONTRACT.md` | OpenAPI version policy and a short list of stable routes |
| `backend/apps/checklist/CHECKLIST_SCHEMA.md` | Declarative schema of the checklist domain |
| `backend/apps/checklist/CHECKLIST_NUMERIC_FORMS_AND_FISHING.md` | Numeric types and daily-log items |
| `backend/apps/core/OFFLINE_SYNC_QUEUE.md` | Queue contract and payloads |
| `backend/apps/core/CLIENT_OFFLINE_LOCAL_SYNC_SCHEMA.md` | Local client / sync states |
| `backend/apps/core/CAPACITOR_VUE_IONIC_OFFLINE_SYNC.md` | Hybrid-app guidelines |

---

*Last consolidation: documentation aligned with the state of the **solidfield_core** repository for the **large-scale industrial fishing** vertical.*
