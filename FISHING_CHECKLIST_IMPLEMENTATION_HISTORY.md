# Implementation history — Checklist + industrial-fishing MVP (SolidField)

This document summarizes **what was done earlier** (documentation, seed, strategy) and **what was done in the continuation** (voyage link, status, CSV export, API/service fixes), in the context of SolidField as a field-operations SaaS.

---

## 1. Context

Product goal: use the **`checklist`** app as the base for an **operational daily log** MVP (diesel, ice, cold-room temperature) for **industrial fishing**, with low UI dependency and data ready for analysis (BI/spreadsheet).

The backend already had checklist models and services; what was missing was documentation standards, a domain template, an explicit binding to the **work order / voyage** (`WorkOrder`), and a simple tabular export.

---

## 2. Work done earlier

### 2.1 Audit and product (documents at the repository root)

- **`MICROSAAS_HEADLESS_AUDIT.md`** — Technical audit of SolidField’s reusable engines (work orders, technician RBAC, offline sync, checklist, geo evidence, reporting), with a Micro-SaaS / headless API view.

### 2.2 Industrial-fishing strategy (Itajaí)

- **`MICROSAAS_INDUSTRIAL_FISHING_ITAJAI.md`** — Mapping of sector pains (diesel, ice, official vessel log, catch share) onto existing modules; MVP recommendation in ~30 days; later evolution of the doc with an **implementation** section (seed, API, export).

### 2.3 Schema of the `checklist/` domain

- **`backend/apps/checklist/CHECKLIST_SCHEMA.md`** — Declarative view: entities, template → execution → submit flow, `answer_type` contracts, APIs, invariants.
- Inclusion of **semantic quality** rules for item generation/completion (do not mix **acquisition** and **contracting**; notes tied to the item’s object; textual flow).

### 2.3.1 Versioned forms + numeric types (diesel, ice, temperature, shift)

- **`backend/apps/checklist/CHECKLIST_NUMERIC_FORMS_AND_FISHING.md`** — Documents the part that was summarized in the product table: how `ChecklistTemplate` / `ChecklistItemTemplate` version the form, how `volume_l`, `weight_kg`, and `temperature` connect to `NUMERIC_CODECS` and `answer_number`, and the table of the 7 fishing daily-log items (per-shift/per-day record).

### 2.4 “Operational daily log — fishing” template (seed)

- **`backend/apps/checklist/defaults/pesca_diario_operacional.py`** — Constants `TEMPLATE_NAME`, `SERVICE_TYPE` (`pesca_industrial_diario`), and the **`ITEM_SPECS`** list with 7 items: shift (text), diesel consumption/refueling/remainder (liters), ice (kg), cold-room temperature (°C), notes in the operational scope.
- Function **`ensure_pesca_diario_operacional_template`**: creates template **version 1** per tenant in an **idempotent** way (if it already exists, it does not duplicate).
- **`backend/apps/checklist/management/commands/seed_pesca_diario_operacional.py`** — Django command to apply the seed (`--tenant-id`, `--technician-id`, `--dry-run`).

Typical command:

```bash
python manage.py seed_pesca_diario_operacional --tenant-id 1 --technician-id 1
```

---

## 3. Work done in the continuation (after “yes, you can continue”)

### 3.1 Checklist ↔ voyage link (`WorkOrder`)

- **`create_checklist`** (`checklist_service.py`) now accepts an optional **`work_order`** and an optional **`filled_by`** (if `filled_by` is omitted, it uses `technician_operating`).
- **Tenant** validation: template, `work_order`, and the filling technician must belong to the same tenant as the operator.
- **`create_checklist_api`**: resolves `template` and `work_order` filtered by `tenant_id`; the body may include `filled_by`; returns explicit errors (`template_not_found`, `work_order_not_found`, and so on).

### 3.2 `draft` / `submitted` lifecycle

- **`Checklist.status`** field (`draft` | `submitted`) added to the model + migration **`0004_checklist_status`**.
- **`submit_checklist`**: on successful submit, sets `status=submitted` and **`incomplete=False`**.
- Serializers now also expose **`incomplete`** alongside `status`.

### 3.3 Bug fixes and consistency

- **`create_checklist`**: fixed use of `errors` before it was declared on the permission-failure path.
- **`bulk_save_answers`**: passes **`technician_operating`** into **`save_answer`** (previously it called without an operator and permission validation broke).
- **`remove_answer`**: on permission failure returns **`False`** (previously it returned `None`, inconsistent with the signature).
- **`Checklist.__str__`**: no longer assumes `work_order` is always set.
- **`ChecklistDetailSerializer`**: correct use of the **`answers`** relation (instead of `checklistitemanswer_set`).
- **`checklist_template_api`**: import of **`next_order_for_template`** adjusted to **`checklist_template_util`** (previously imported incorrectly from the service).

### 3.4 CSV export for BI / Excel

- New module **`backend/apps/checklist/services/checklist_export_service.py`**: builds a CSV with one row per answer (and an “empty” item row when the checklist has no answers), including voyage, template, and technician identifiers plus answer columns.
- New endpoint **`GET /export_checklist_answers_csv_api/`** (registered in **`backend/apps/apis/urls.py`**), with optional query filters:
  - `work_order_id`
  - `service_type` (for example `pesca_industrial_diario`)
  - `template_id`
  UTF-8 file with **BOM** so it opens cleanly in Excel.

### 3.5 Documentation updated

- **`CHECKLIST_SCHEMA.md`** — Attention section updated (resolved items + remaining gaps); export route included.
- **`MICROSAAS_INDUSTRIAL_FISHING_ITAJAI.md`** — Section 7.3 describing the `WorkOrder` link and CSV export; 7.4 with optional next steps.

### 3.6 Cleanup

- Removed the stray **`command.txt`** file inside `management/commands/` (example commands duplicated what is already in the fishing doc).

### 3.7 Offline queue (`OfflineSyncQueue`)

- **`OfflineSyncQueue`** model: **`client_mutation_id`** field + partial *unique* per technician (idempotency); `related_name` **`offline_sync_items`**.
- Migration **`core/0004_offlinesyncqueue_client_mutation.py`**.
- Permissions **`enqueue_offline_sync`** and **`process_offline_sync`** in **`permission_schemas.py`** (L1 + L2/L3 inheritance).
- Service **`core/services/offline_sync_service.py`**: enqueue, list the technician’s queue, process an item with a *lock* (`select_for_update`); actions **`checklist_batch_answers`** and **`checklist_submit`**; reprocessing of **`conflict`**; **`success`** is idempotent on process.
- APIs: **`enqueue_offline_sync_api`**, **`list_offline_sync_api`**, **`process_offline_sync_api/<queue_id>/`** in **`core/api/offline_sync_api.py`**, routes in **`apis/urls.py`**.
- Doc **`backend/apps/core/OFFLINE_SYNC_QUEUE.md`**; basic tests in **`core/tests/test_offline_sync_service.py`**.

---

## 4. Recommended operational order

1. Run migrations: `python manage.py migrate` (`checklist` app for the `status` field).
2. Seed the fishing template per tenant: `seed_pesca_diario_operacional`.
3. Create or use a voyage **`WorkOrder`** (same tenant).
4. **`POST create_checklist_api/`** with `template` + `work_order`.
5. **`POST create_checklist_item_answer_api/`** to save answers.
6. **`GET export_checklist_answers_csv_api/`** with the desired filters for external analysis.

---

## 5. Main files (quick reference)

| Area | Files |
|------|-------|
| Strategy / audit | `MICROSAAS_HEADLESS_AUDIT.md`, `MICROSAAS_INDUSTRIAL_FISHING_ITAJAI.md` |
| Checklist schema | `backend/apps/checklist/CHECKLIST_SCHEMA.md` |
| Fishing seed | `backend/apps/checklist/defaults/pesca_diario_operacional.py`, `.../management/commands/seed_pesca_diario_operacional.py` |
| Checklist service + API | `backend/apps/checklist/services/checklist_service.py`, `.../api/checklist_api.py` |
| CSV export | `backend/apps/checklist/services/checklist_export_service.py` |
| Status model + migration | `backend/apps/checklist/models/checklist.py`, `.../migrations/0004_checklist_status.py` |
| Offline queue | `backend/apps/core/models/sync.py`, `core/migrations/0004_offlinesyncqueue_client_mutation.py`, `core/services/offline_sync_service.py`, `core/api/offline_sync_api.py`, `OFFLINE_SYNC_QUEUE.md` |
| Routes | `backend/apps/apis/urls.py` |

---

## 6. What has not been done yet (outside this history)

- Automatic integration with **`filehub`** (meter/thermometer photo) per item.
- A **catch-share** engine or a complete **legal** official vessel log (a specific regulatory PDF).
- Dedicated frontend screens; the MVP assumes APIs + CSV + an HTTP/spreadsheet client.

This file is **implementation memory** only; business and compliance rules must be validated with specialists and the competent authorities before use in regulated production.
