# Guide — next steps to connect Filehub and **sf-watermarker-worker-go**

Operational document for the **Django (solidfield_core)** and **Go / DevOps** teams. Complements `FILEHUB_SF_WATERMARKER_INTEGRATION_ANALYSIS.md` and `SF_WATERMARKER_SOLIDFIELD_INTEGRATION.md` (repository root).

---

## Reading prerequisite

- Microservice HTTP contract: `POST /image_watermark_service_webhook`, header **`X-Tenant-ID`**, response **`202`** + `job_id` (+ `tenant_id`). Processing is **asynchronous** (NATS). Closing the loop back to Filehub follows **decision (A)** below (object storage + webhook).

---

## Recorded decision — delivery of the final JPEG (**option A**)

**Product / architecture choice (solidfield_core + sf-watermarker-worker-go):**

1. The **worker** sends the processed JPEG to **object storage** compatible with the **S3 API** (AWS S3, MinIO, and so on).
2. The worker (or a component attached to the pipeline) calls a **webhook on Django** with, at minimum: **`job_id`**, identification of the record (`work_order_photo_id` or an agreed equivalent), and the **object location** (**signed URL** and/or **bucket + key**).
3. Django validates the request (mutual authentication to be defined on line **0.2**) and updates **`WorkOrderPhoto`** (and `watermark_status` / final file fields as the model defines) in an **idempotent** way.

> **Note:** until this extension exists in Go, the worker still writes only to `OUTPUT_DIR`; decision (A) defines the implementation **target**, not the current state of the binary.

---

## Phase 0 — Cross-team agreement (remaining)

| # | Decision | State | Notes |
|---|----------|-------|-------|
| 0.1 | **Final JPEG delivery** | **✓ (A)** Object storage (S3/MinIO) + Django **webhook** (`job_id`, URL or key) | See the previous section. Options (B) poll and (C) volume are **not** the official path. |
| 0.2 | **Security** Django ↔ Go (+ completion webhook) | Open | API key, HMAC, mTLS, private network; also protect the callback endpoint. |
| 0.3 | **`X-Tenant-ID`** | Open | For example `str(CompanyTenant.pk)` or `tenant_code` — align with the callback payload. |

---

## Phase 1 — Original image reachable by the worker (URL / storage)

Go issues a **GET** on `image_url` with **anti-SSRF** (private IPs blocked by default).

| # | Task | Detail |
|---|------|--------|
| 1.1 | Define **storage** in prod | Local `MEDIA_*` vs. **S3** (`django-storages` or equivalent). |
| 1.2 | Guarantee a URL the **Go container can read** | Prefer a **signed URL** (short TTL) for the object; avoid depending on the Django private IP without a clear policy. Alternative: **`image_base64`** on the webhook (heavier). |
| 1.3 | Document use of `ALLOW_PRIVATE_IPS` in Go | **Development only**; never as a production solution. |

---

## Phase 2 — Django model `WorkOrderPhoto`

| # | Task | Suggested fields (adjust per product) |
|---|------|---------------------------------------|
| 2.1 | Migration | `watermark_job_id` (UUID/string, nullable until the first enqueue) |
| 2.2 | | `watermark_status`: for example `none`, `pending`, `processing`, `completed`, `failed` |
| 2.3 | | `watermark_error` (short text, optional) |
| 2.4 | Product decision | **One** image (replace `image` after watermark) vs. **two** (`image` original + `image_watermarked` or a storage URL) |

Current file: `backend/apps/filehub/models/os_photo.py`.

---

## Phase 3 — Django HTTP client → sf-watermarker-worker-go

| # | Task | Detail |
|---|------|--------|
| 3.1 | Settings | `WATERMARKER_BASE_URL`, timeouts, retry policy |
| 3.2 | Build `WebhookPayload` from the model | `work_reference` ← `WorkOrder.identifier`; `uploaded_by` ← technician (name or id); `photo_taken_at`, GPS, `device_info`, `add_watermark`, `watermark_has_company_logo`; `company_logo_url` ← public URL of `CompanyTenant.logo` if it exists |
| 3.3 | `X-Tenant-ID` header | Value agreed in phase 0.3 |
| 3.4 | Map **`photo_type`** | Django choices (`before`, `after`, `issue`, `proof`, `custom`) vs. the Go whitelist — align or use a mapping table |
| 3.5 | After `202` | Store `watermark_job_id` and `watermark_status=pending` (or `processing`) |

Recommended implementation: a dedicated module, for example `backend/apps/filehub/services/watermark_client.py` (name chosen by the team).

---

## Phase 4 — When to trigger the watermarker

| # | Task | Detail |
|---|------|--------|
| 4.1 | **`transaction.on_commit`** | Call the HTTP client **after** the commit that persists `WorkOrderPhoto` and the file — avoids jobs if the transaction fails |
| 4.2 | `add_watermark` flag | If `False`, do not send to Go (or send only a “JPEG normalization” pipeline, if agreed with the Go team) |
| 4.3 | Network failures | Idempotent retry: decide whether the same `job_id` can be reused or a new row/record is created |

---

## Phase 5 — Completion endpoint on Django (when phase 0.1 = callback)

| # | Task | Detail |
|---|------|--------|
| 5.1 | Internal route | For example `POST /internal/watermark-complete/` (do not expose it to the internet without protection) |
| 5.2 | Body | `job_id`, state, final JPEG URL or content referenced by an S3 key |
| 5.3 | Update `WorkOrderPhoto` | Fill the final-image field(s) + `watermark_status=completed` or `failed` |
| 5.4 | **Idempotency** | The same `job_id` may be notified more than once |

---

## Phase 6 — Public Filehub API (field app)

| # | Task | Detail |
|---|------|--------|
| 6.1 | `POST` (multipart) | Create a `WorkOrderPhoto` for a `work_order_id`; validate tenant and technician |
| 6.2 | `GET` | List / detail photos for the work order |
| 6.3 | OpenAPI | `@extend_schema` with stable `operation_id` values (Public v1), aligned with `API_PUBLIC_CONTRACT.md` |
| 6.4 | Registration | Include routes in `backend/apps/apis/urls.py` |

---

## Phase 7 — Recommended cleanups (parallel)

| # | Task | Where |
|---|------|-------|
| 7.1 | Fix use of `work_order.from_user` | `backend/apps/core/services/audition_log_service.py` — `WorkOrder` has `created_by`, not `from_user` |
| 7.2 | Fix tests | `backend/apps/filehub/tests/test_photo.py` — use `work_order`, `photo_taken_at`; `test_signature.py` — import `WorkOrderSignature` |

---

## Phase 8 — After the MVP (does not block the first thread)

| # | Task | Detail |
|---|------|--------|
| 8.1 | Optional checklist / item FK | `WorkOrderPhoto` → `Checklist` / `ChecklistItemTemplate` (fishing MVP) |
| 8.2 | `OfflineSyncQueue` | New action for offline photo upload — quotas, maximum size, retry |

---

## Suggested order in a sprint

1. **Phase 0** — `0.1` **closed** (S3/MinIO + webhook); close **`0.2`** security and **`0.3`** `X-Tenant-ID` + callback format.
2. **Phase 1** + **Phase 2** in parallel (DevOps + Django).
3. **Phase 3** + **Phase 4** (asynchronous trigger working with `202`).
4. **Phase 5** as soon as Go (or the orchestrator) delivers the close-out (callback/storage).
5. **Phase 6** for the app.
6. **Phase 7** when possible.
7. **Phase 8** according to the fishing roadmap.

---

## Related documents

| File | Contents |
|------|----------|
| `FILEHUB_SF_WATERMARKER_INTEGRATION_ANALYSIS.md` | Current-state analysis vs. gaps |
| `FILEHUB_FISHING_MVP_BRIEFING.md` | Fishing product + checklist extension |
| `SF_WATERMARKER_SOLIDFIELD_INTEGRATION.md` | Technical contract of the Go microservice |
| `LARGE_SCALE_INDUSTRIAL_FISHING_DOCUMENTATION.md` | Macro view of the vertical |

---

*Working guide — update it when the callback/storage and internal routes are defined in code.*
