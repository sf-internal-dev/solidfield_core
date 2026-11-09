# Briefing for the Filehub system — integration with the industrial-fishing MVP

**Recipient:** team / owners of **Filehub** in the SolidField ecosystem.
**Purpose of this document:** ask Filehub to return a **detailed technical `.md`** describing how the module actually works (APIs, data model, rules, limits), so we can bind **photographic evidence (and, if applicable, signatures)** to the **Operational daily log — industrial fishing** flow without reinventing contracts.

**Expected response:** a Markdown file (for example `FILEHUB_TECHNICAL_SPECIFICATION.md`) covering the topics in section 6.

---

## 1. Product context (checklist / fishing side)

- The **large-scale industrial fishing** vertical uses the `checklist` app with the seeded template **`pesca_industrial_diario`** (`service_type`: `pesca_industrial_diario`), with items such as diesel consumption (L), ice (kg), cold-room temperature (°C), shift, and notes.
- Each checklist **execution** can be linked to a **`WorkOrder`** (voyage / work order) via an optional field on checklist creation.
- The **server** already exposes checklist APIs, CSV export, work orders, and the **offline queue** (`OfflineSyncQueue`) for answer batches and submit — see `LARGE_SCALE_INDUSTRIAL_FISHING_DOCUMENTATION.md` at the repository root.
- **Product need:** attach **photos with field context** (for example hour-meter/fuel panel, thermometer reading, ice condition) to reduce disputes and support audit. Ideally the evidence is **findable** by the combination **voyage (`work_order_id`) + checklist + template item** (or an agreed “evidence type” code).

---

## 2. What Filehub is **today** in this repository (actual state)

In the current `solidfield_core` code, the `backend.apps.filehub` app mainly contains **Django models** and **admin**, not REST routes listed in `backend/apps/apis/urls.py`.

### 2.1 `WorkOrderPhoto`

- **Link:** `ForeignKey` to `orders.WorkOrder` (`related_name="photos"` on the model).
- **Who uploaded:** `ForeignKey` to `core.Technician` (`uploaded_by`).
- **File:** `ImageField` (`upload_to="service_photos/"`).
- **Time:** `photo_taken_at` (required on the model), `uploaded_at` (auto on create).
- **Semantic type:** `photo_type` — values: `before`, `after`, `issue`, `proof`, `custom`.
- **Optional:** `description`, `gps_latitude`, `gps_longitude`, `device_info`, `add_watermark`, `watermark_has_company_logo`.

File: `backend/apps/filehub/models/os_photo.py`.

### 2.2 `WorkOrderSignature`

- **Link:** `ForeignKey` to `orders.WorkOrder` (`related_name="signature"` on the model).
- **Order / client:** `ordered_by` (technician), `signed_by` (text), `image`, `signed_at`, optional `latitude`, `longitude`, `ip_address`.

File: `backend/apps/filehub/models/os_signature.py`.

### 2.3 Integrations already touched

- **Admin:** photo and signature inlines on the work order (`orders` admin).
- **Audit:** functions in `backend/apps/core/services/audition_log_service.py` that refer to photo/signature upload (align `action_code` and use of `work_order.from_user` with the real `WorkOrder` model when you document this).

### 2.4 Explicit gap

- There are **no** public endpoints documented in the “Public v1” OpenAPI for Filehub file upload/listing at this step.
- Filehub models have **no** `ForeignKey` to `checklist.Checklist` or `ChecklistItemTemplate` — today the natural link is only **`WorkOrder` + metadata** (`photo_type`, `description`).

---

## 3. What the “Fishing MVP” flow needs from Filehub

| Need | Detail |
|------|--------|
| Upload from the field app | Multipart or pre-signed URL; authentication aligned with the technician / tenant. |
| Minimum binding | `work_order_id` required; **desirable optional:** `checklist_id`, `checklist_item_template_id`, or an `evidence_code` string to cross-reference the daily log. |
| Metadata | Optional GPS, capture timestamp, photo type (reuse `photo_type` or an enum extended for fishing). |
| Listing / download | So the technician or back office can see voyage evidence (and, later, a combined export with the checklist CSV). |
| Multi-tenant | Isolation consistent with `WorkOrder.tenant` / technician. |
| Offline | The client may store photos locally; on sync we need a **strategy** (direct upload vs. an `OfflineSyncQueue`-style queue with an upload payload — to be defined with you). |

**End-customer** signature can stay **outside the fishing MVP** (the focus is operational evidence photos).

---

## 4. Proposed model extension (for discussion)

If you want to bind “photo of daily-log item 6” without ambiguity, one of these options:

- **A)** Optional fields on `WorkOrderPhoto`: `checklist`, `checklist_item_template` (or nullable integer IDs only).
- **B)** Keep only `WorkOrder` + a standardized `description` / `photo_type` (`custom` + text such as `checklist:123:item:45`).
- **C)** An N:N link table or a separate “AttachmentMetadata” model.

We need your recommendation (**performance, migrations, Filehub’s current pattern**).

---

## 5. What this project will deliver back after your documentation

- DRF routes (or consumption of your service) aligned with the contract you describe.
- Possible extension of `OfflineSyncQueue` actions to **record a pending upload**, if the flow is asynchronous.
- Public v1 OpenAPI update for evidence operations, if that is part of the closed MVP package.

---

## 6. Checklist of what we ask for in the return `.md` (detailed)

Please include:

1. **Inventory:** models, relations, `upload_to`, storage (local/S3/etc.), maximum size, accepted formats.
2. **Existing or planned APIs:** method, path, auth, body, responses, error codes, pagination.
3. **Permissions:** which RBAC action / technician level can create, list, and delete attachments.
4. **Watermark / post-processing:** whether it is synchronous, queued, or only a flag on the model.
5. **Public vs. internal URLs:** how the app obtains thumbnails or a secure download.
6. **Audit:** events fired on upload; consistency with `audition_log_service`.
7. **Multi-tenant:** validations when associating `work_order_id` with the authenticated technician.
8. **Signatures:** when to use `WorkOrderSignature` vs. a photo; legal requirements you know of.
9. **Known limitations** and a short Filehub roadmap.
10. **Complete example:** the flow “create work order → take photo → associate → list” with `curl` or equivalent.

---

## 7. Logical contact between teams

- **Primary consumer:** `checklist` app + APIs in `backend/apps/apis/urls.py` + the `core` queue (offline).
- **Checklist domain documentation:** `backend/apps/checklist/CHECKLIST_SCHEMA.md`.
- **Fishing seed items:** `backend/apps/checklist/defaults/pesca_diario_operacional.py` (item names and order, to align evidence codes).

---

*Document generated for the Filehub ↔ Fishing MVP vertical handoff. Adjust dates and decision owners to match your internal process.*
