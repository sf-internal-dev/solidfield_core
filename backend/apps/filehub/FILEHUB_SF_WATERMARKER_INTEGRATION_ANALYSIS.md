# Analysis — Filehub + **sf-watermarker-worker-go** in solidfield_core

This document crosses the **actual** state of the `filehub` app in this repository with the specification **`SF_WATERMARKER_SOLIDFIELD_INTEGRATION.md`**, to guide the integration work (Django APIs, model, security, closing the asynchronous loop).

---

## 1. Current state of Filehub (code)

| Aspect | Situation |
|--------|-----------|
| **Models** | `WorkOrderPhoto`, `WorkOrderSignature` — both linked to `orders.WorkOrder` + `Technician`. |
| **REST APIs** | There are **no** entries in `backend/apps/apis/urls.py` for photo or signature upload/listing. |
| **Operational use** | Mostly **Django Admin** (inlines on `WorkOrder`). |
| **Alignment with the watermarker** | `WorkOrderPhoto` already has `add_watermark`, `watermark_has_company_logo`, and metadata (GPS, `device_info`, `photo_taken_at`, `photo_type`) — they **mirror the semantic contract** of the Go webhook. |
| **Checklist / fishing** | **No FK** to `Checklist` or `ChecklistItemTemplate`; the link to the daily log today is only via the **same `WorkOrder`** plus text in `description` / convention (see `FILEHUB_FISHING_MVP_BRIEFING.md`). |
| **Tests** | `test_photo.py` uses `service_order` and omits `photo_taken_at` — **out of line** with the current model (`work_order`, `photo_taken_at` required). `test_signature.py` imports `ServiceOrderSignature` (a name that does not exist). **The filehub test suite does not reflect the code.** |
| **Audit** | `log_work_order_photo_upload` / `log_work_order_client_signature_upload` use `work_order.from_user`; on `WorkOrder` the field is **`created_by`**, not `from_user` — a **bug / technical debt** when wiring a real upload. |
| **Media / storage** | `ImageField` with a local `upload_to`; `settings.py` **does not define** `MEDIA_URL` / `MEDIA_ROOT` explicitly (common in dev; production is usually S3 or a served path). That implies a **clear URL strategy** so Go can `GET` the original image. |

---

## 2. State of **sf-watermarker-worker-go** (contract summary)

| Aspect | Implication for the core |
|--------|--------------------------|
| Entry | `POST /image_watermark_service_webhook`, JSON; **`X-Tenant-ID` required**. |
| Image | `image_url` **or** `image_base64`. |
| Response | **`202`** + `{ job_id, tenant_id }` — **asynchronous** processing (NATS JetStream). |
| Output | File **`{OUTPUT_DIR}/{job_id}.jpg`** on the worker disk — it **does not update** Django or Filehub. |
| URL security | Anti-**SSRF**: private IPs blocked by default (`ALLOW_PRIVATE_IPS=true` for dev only). |
| `photo_type` | The Go whitelist may **not match** Django `PHOTO_TYPE_CHOICES` (`before`, `after`, `issue`, `proof`, `custom`) — needs a **mapping** or an enum extension on one side. |
| Company logo | `company_logo_url` (HTTP(S)); the core has `CompanyTenant.logo` — a natural candidate to originate a **public** URL (or a signed proxy). |

---

## 3. Central gap: close the loop **original → job → final image in Filehub**

The watermarker doc describes the gap correctly:

1. Today Go does **not** callback and does **not** write to product storage.
2. The core does **not** persist `job_id` or a state (`pending` / `done` / `failed`).
3. **One** of the patterns below is required (order = pragmatic recommendation).

### Option A — Object storage + notification (best for production) — **DECISION ADOPTED**

This is the path chosen for **solidfield_core**: close the loop with **S3-compatible storage + a completion webhook** to Django (see `FILEHUB_WATERMARKER_NEXT_STEPS.md`).

1. After the worker generates the JPEG, **send it to S3** (or a single bucket path per tenant).
2. **Completion webhook** to Django with `job_id`, the final URL and/or **bucket + key**, and the record identifier (`work_order_photo_id` or equivalent).
3. Django updates `WorkOrderPhoto` (`image` field or a separate `image_watermarked` field) and `watermark_status=done` (idempotent).

### Option B — Poll `GET /jobs/{id}` + download (Go service extension)

- Requires implementation **in the watermarker**; the doc states it **does not exist yet**.

### Option C — Shared volume / agent

- Django or an agent copies `{job_id}.jpg` into `MEDIA_ROOT` and updates the record.
- Fragile on Kubernetes/multi-instance; useful only in dev or on a single node.

**Conclusion:** without **A or B**, Filehub is not “integrated end to end” — it only **fires** the job.

---

## 4. Critical problem: an **`image_url` the worker can read**

The worker `GET`s the URL with a 15s timeout. To use a **photo already stored** in Django:

- The URL must be **reachable from the network where the Go container runs** (a local path is not enough).
- If the URL points at **Django behind a private IP** (for example `http://10.x/.../media/...`), Go **rejects** it for SSRF — correct in prod.
- **Typical mitigations:**
  - a **signed URL** (S3/MinIO), temporarily public on the same network the worker can reach without being a poorly defined internal “private IP”; or
  - the **same VPC** with a controlled exception (document the risk); or
  - **base64** on the webhook (heavy for large photos, but it avoids the fetch).

This must be decided together with **DevOps** and the watermarker documentation (`ALLOW_PRIVATE_IPS` for dev only).

---

## 5. `WorkOrderPhoto` model — fields to consider in the integration

| Existing field | Use with the watermarker |
|----------------|--------------------------|
| `image` | Keep the **original** until there is a clear policy; or replace it with the **final version** after watermark (the original is lost unless the field is duplicated). |
| `add_watermark` / `watermark_has_company_logo` | Control whether the webhook is called and `company_logo_url`. |
| *(proposed)* `watermark_job_id` | UUID returned on `202`. |
| *(proposed)* `watermark_status` | for example `pending`, `processing`, `completed`, `failed` — or reuse simple flags. |
| *(proposed)* `image_original` | If the product wants to **keep** original + watermarked (2 files). |

**Product decision:** one image only (replace) vs. two (compliance / dispute).

---

## 6. `X-Tenant-ID` — what to send

The header is required in Go. Agree on a stable value:

- **`str(CompanyTenant.pk)`** (simple); or
- **`tenant_code`** / **slug** (if it is unique and immutable enough).

The same value must appear in logs and in future completion-webhook correlations.

**Note:** this **does not replace** RBAC in Django; it is a label for the worker and JetStream.

---

## 7. Recommended flow (high level) for implementation in the core

1. **API** `POST` upload (multipart) → creates `WorkOrderPhoto` with the original file, validates `work_order.tenant` vs. the technician.
2. If `add_watermark`:
   - Build the webhook payload (field mapping in section 8 of `SF_WATERMARKER_SOLIDFIELD_INTEGRATION.md`).
   - Obtain an `image_url` **valid for the worker**, OR send `image_base64`.
   - `POST` to Go with `X-Tenant-ID`.
   - Persist `job_id` + `watermark_status=pending`.
3. **Asynchronous:** the worker processes → **(not implemented yet)** final delivery → Django updates the photo + `watermark_status=completed`.
4. If `add_watermark=False`, it can still optionally call Go for “JPEG normalization only”, according to the service flag — see the Go doc.

**Technical trigger:** `post_save` signal, Celery, `transaction.on_commit` + async HTTP, or a dedicated command — avoid blocking the request if Go is slow (although `202` is fast, the network can fail).

---

## 8. Offline (`OfflineSyncQueue`) and photos

- Checklist answers already have actions on the queue; **photos** can be:
  - a **direct** upload when the network is up (multipart to a new API), or
  - a new `filehub_photo_upload` action with a payload (metadata + chunked base64 or a reference to a local blob) — **more work**, plus size limits.
- MVP recommendation: **online upload first**; offline photos as **phase 2** with a quota and retry design.

---

## 9. “Public v1” OpenAPI

- Filehub endpoints should receive `@extend_schema` with stable `operation_id` values when they exist, aligned with the rest of the contract (`API_PUBLIC_CONTRACT.md`).

---

## 10. Cross documentation

| File | Role |
|------|------|
| `SF_WATERMARKER_SOLIDFIELD_INTEGRATION.md` | Go microservice contract; gaps and patterns A/B/C. |
| `FILEHUB_FISHING_MVP_BRIEFING.md` | Fishing product request + checklist extension. |
| `LARGE_SCALE_INDUSTRIAL_FISHING_DOCUMENTATION.md` | Macro view of the vertical. |

**Note:** `SF_WATERMARKER_SOLIDFIELD_INTEGRATION.md` references `HANDOFF_BACKEND_FILEHUB_PESCA_INDUSTRIAL.md` — a **file that does not exist** in this repo; use `FILEHUB_FISHING_MVP_BRIEFING.md` or this document as the Django reference.

---

## 11. Engineering work checklist

- [ ] Fix `filehub` tests and `audition_log_service` (`from_user` → `created_by` or `uploaded_by`).
- [ ] Define `MEDIA_*` / storage aligned with a URL for the worker.
- [ ] Implement Filehub APIs + permissions.
- [ ] HTTP client to the watermarker (timeouts, idempotent retries with the same `job_id` when applicable).
- [ ] Migration: `watermark_job_id`, `watermark_status` (+ optional second file).
- [ ] Close the loop: **Go callback** or **S3 + event** (agree with the watermarker repo).
- [ ] Map Django `photo_type` ↔ Go validation.
- [ ] (Optional) Optional FK `WorkOrderPhoto` → checklist / item template for the fishing MVP.
- [ ] Document `X-Tenant-ID` and security (API key / mTLS between Django and Go in production — today the webhook only validates the tenant header).

---

*Consolidated analysis to align Filehub development with **sf-watermarker-worker-go**.*
