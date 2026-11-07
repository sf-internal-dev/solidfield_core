# sf-watermarker-worker-go — technical specification and integration with SolidField (Filehub / solidfield_core)

**Audience:** backend teams (Django), Filehub, DevOps, product.
**Scope of this repository:** the code of **this** project; the link to **solidfield_core** is described in terms of the **target contract and architecture**, except where the opposite is stated explicitly.

---

## 1. What sf-watermarker-worker-go is

It is a **standalone microservice** in **Go** whose only responsibility is:

1. Receive a request to **process an image** (arriving by **HTTP(S) URL** or **base64**).
2. Optionally apply a **watermark** (metadata panel + logos).
3. **Enqueue** the work and respond immediately with a job identifier (**asynchronous**).
4. A **worker** consumes the queue, processes, and **writes the result** as a **JPEG** in a configurable directory (`OUTPUT_DIR`).

It does not manage users, work-order permissions, definitive product storage, or checklist — that belongs to **solidfield_core** (Django) and the **Filehub** module. This service is an **image engine + queue** meant to be called **from** the SolidField ecosystem (or another orchestrator) when `add_watermark` (or an equivalent rule) is active.

---

## 2. Product and technical objectives

| Objective | Description |
|-----------|-------------|
| **Decouple** heavy image processing from the Django API | Avoid timeouts and block fewer WSGI/ASGI workers during decode, resize, and composition. |
| **Scale horizontally** | Several processes of the same binary with different **NATS consumers** (`NATS_CONSUMER`). |
| **Field metadata on the image** | Readable text (technician, date, GPS, context, job, device) for **audit** and fewer disputes (aligned with verticals such as industrial fishing / checklist). |
| **Visual marks** | The **software** logo (embedded in the binary) and, optionally, the **company** logo (HTTP URL). |
| **Real phone formats** | Decode pipeline with **EXIF/orientation**; **HEIF/HEIC/AVIF** with a `heif` + CGO build (see the README). |

---

## 3. Stack and components

| Component | Technology | Role |
|-----------|------------|------|
| HTTP API | **Gin** | JSON webhook, health checks. |
| Queue | **NATS JetStream** | Work-queue stream, configurable subject, `MsgId` = `job_id` (deduplication on publish). |
| Image processing | `disintegration/imaging`, `golang.org/x/image`, **goexif**, optionally **goheif** | Resize, overlay, text, JPEG orientation, HEIF. |
| Persistence **in this service** | Local filesystem | `{OUTPUT_DIR}/{job_id}.jpg` — this is **not** the Django `ImageField`. |
| Tenancy on the API | Header **`X-Tenant-ID`** | Required for the webhook; it is **echoed** in the 202 response and stored on the queue message; it does **not** replace RBAC in the core. |

---

## 4. Execution architecture (single process)

On startup (`cmd/main.go`):

1. Ensures `OUTPUT_DIR`.
2. Loads the **software logo** (PNG embedded in `assets/`).
3. Connects to **NATS**, creates the JetStream stream if it does not exist (~24h message retention).
4. Instantiates **`FileStorage`** + **`Worker`** (with `MAX_DIM`).
5. Subscribes the consumer and starts a **goroutine** that pulls/fetches messages (explicit ack: success → `Ack`, failure → `Nak` / retry).
6. Starts the Gin **HTTP server** in another goroutine.
7. **Graceful shutdown** of the process: SIGINT/SIGTERM (HTTP may end abruptly depending on the current implementation).

Flow of one job:

```
HTTP client ──POST /image_watermark_service_webhook──► Gin
       │ validates JSON + tenant
       ▼
  generates job_id (UUID)
       ▼
  publishes JobMessage on JetStream (MsgId = job_id)
       ▼
  responds 202 { job_id, tenant_id }

Worker (loop) ──fetch──► deserializes JobMessage
       ▼
  loads the image (URL or base64)
       ▼
  resize if > MAX_DIM
       ▼
  if add_watermark: compose + logos; otherwise: write only
       ▼
  SaveImage(job_id) → OUTPUT_DIR/{job_id}.jpg
       ▼
  Ack the NATS message
```

---

## 5. HTTP API (current contract)

### 5.1 Endpoints

| Method | Path | Response |
|--------|------|----------|
| `GET` | `/healthz` | `200` text `ok` |
| `GET` | `/readyz` | `200` text `ready` |
| `POST` | `/image_watermark_service_webhook` | See below |

### 5.2 Webhook — authentication and errors

- **Tenant:** header **`X-Tenant-ID`** required and non-empty. If missing → **`401`** `{ "error": "unauthorized" }`.
- **Body:** JSON; parse failure → **`400`** `bad_request`.
- **Business validation** → **`400`** `invalid_payload` with a `fields` or `details` map.
- **Queue unavailable** (publish failure) → **`503`** `queue_unavailable`.

### 5.3 JSON body (`WebhookPayload`)

Fields (mirrored in `internal/httpapi/types.go` and `internal/queue/types.go` — they must stay aligned):

| JSON field | Type | Notes |
|------------|------|-------|
| `image_url` | string | At least one of `image_url` or `image_base64`. |
| `image_base64` | string | Standard base64 of the image. |
| `photo_type` | string | For example `installation`, `maintenance` (partial validation / whitelist in `validators.go`). |
| `uploaded_by` | string | **Required** (audit / overlay). |
| `photo_taken_at` | string | ISO 8601 when set. |
| `work_reference` | string | For example the work-order code — useful for the “Work: …” overlay. |
| `location_label` | string | Human-readable location text. |
| `photo_context` | string | For example before/after an installation. |
| `add_watermark` | bool | If `false`, only normalizes and writes a JPEG without the panel. |
| `watermark_has_company_logo` | bool | If `true` and watermark is active → requires `company_logo_url`. |
| `watermark_has_software_logo` | bool | Includes the embedded SolidField logo. |
| `gps_latitude` / `gps_longitude` | optional float64 | Both or neither. |
| `device_info` | string | Overlay. |
| `company_logo_url` | string | HTTP(S); anti-SSRF validation (private-IP block unless `ALLOW_PRIVATE_IPS=true`). |

### 5.4 Success response (enqueue)

**`202 Accepted`**

```json
{
  "job_id": "<uuid>",
  "tenant_id": "<value of the X-Tenant-ID header>"
}
```

### 5.5 URL security

- Schemes `http` / `https` only.
- **Anti-SSRF:** IPs in private networks, loopback, link-local, and IPv6 ULA are **rejected** by default; in development, `ALLOW_PRIVATE_IPS=true` may be used.

---

## 6. NATS JetStream queue

| Variable | Default |
|----------|---------|
| `NATS_URL` | `nats://localhost:4222` |
| `NATS_STREAM` | `WATERMARK_JOBS` |
| `NATS_SUBJECT` | `watermark.jobs` |
| `NATS_CONSUMER` | `watermark-worker-1` |

**Message (`JobMessage`):** `{ "job_id", "tenant_id", "payload": { ... the same webhook JSON ... } }`.

**Behavior:** work queue, `MaxAckPending` 100, fetch of 1 message with a wait of up to 5s, retry on processing failure.

**Operational limitation:** the result stays only on the **local disk** of this service; there is **no** HTTP notification back to Django in this version of the code.

---

## 7. Image pipeline (summary)

1. **Source:** `internal/source` — GET with a 15s timeout and `User-Agent` / `Referer` headers, or base64 decode.
2. **Decode:** `internal/imaging.DecodeImageWithEXIF` — PNG, JPEG+EXIF orientation, HEIF/AVIF sniff (with the `heif` tag), generic fallback (for example WebP).
3. **Resize:** `imaging.Fit` up to `MAX_DIM` (default 1600).
4. **Composition:** `internal/compose.ComposeWatermark` — frame, bottom-right panel with text (wrap), highlight bar, shadows; logos above the panel.
5. **Write:** `internal/storage` — JPEG quality 92, name `{job_id}.jpg`.

**Embedded fonts:** `assets/` (WorkSans + logo) via `go:embed`.

---

## 8. Where solidfield_core and Filehub come in

**solidfield_core** is the **Django monolith** (APIs, tenants, technicians, **WorkOrder**, **checklist**, and so on). **Filehub** is the Django app that models attachments linked to the work order, namely **`WorkOrderPhoto`** (`backend/apps/filehub/models/os_photo.py`).

### 8.1 Semantic alignment (already anticipated in the models)

The `WorkOrderPhoto` model includes fields that **map naturally** to this service’s webhook:

| Filehub concept (Django) | Field / use | Go webhook |
|--------------------------|-------------|------------|
| Photo file | `ImageField` — after upload, a **public or signed** URL the worker can read | `image_url` |
| Alternative | Binary body in base64 (less common for large photos) | `image_base64` |
| Who uploaded | `uploaded_by` (FK Technician → use name or id in the string) | `uploaded_by` |
| Capture time | `photo_taken_at` | `photo_taken_at` |
| Semantic type | `photo_type` (`before`, `after`, `issue`, `proof`, `custom`) | `photo_type` (may require a **mapping** or an enum extension on one side) |
| GPS | `gps_latitude`, `gps_longitude` | `gps_latitude`, `gps_longitude` |
| Device | `device_info` | `device_info` |
| Watermark | `add_watermark`, `watermark_has_company_logo` | `add_watermark`, `watermark_has_company_logo` |
| Company logo | URL configurable per tenant / future field | `company_logo_url` |
| Job reference | `WorkOrder` code or an external reference | `work_reference` |
| Checklist / fishing context | `description` or future FKs (`checklist`, item) | `photo_context`, `location_label` |

The Django **tenant** must be propagated as **`X-Tenant-ID`** on the request to the microservice (a stable value agreed between systems — for example the tenant slug or UUID).

### 8.2 What is **not** implemented in this repository

- HTTP calls **from** `solidfield_core` **to** this service.
- A Django model field `watermark_job_id` or states `pending/processing/done`.
- A **callback** from the Go worker to update `WorkOrderPhoto` or send the final file to the **same** `ImageField` / S3.
- Mutual authentication (HMAC, mTLS, API key) between Django and Go — the current webhook only requires `X-Tenant-ID`.

This is **integration still to be built** in the core (and, optionally, hardening in Go).

### 8.2.1 Architecture decision in **solidfield_core** (recorded)

The **SolidField / Filehub** ecosystem adopted **pattern A** for delivery of the final JPEG:

- **sf-watermarker-worker-go** (after implementation) **writes the result to object storage** (an S3-compatible API, for example MinIO) and invokes a **webhook on Django** with `job_id`, a reference to the `WorkOrderPhoto` (or an agreed internal id), and a **signed URL** and/or **bucket + key**.
- Operational detail: `backend/apps/filehub/FILEHUB_WATERMARKER_NEXT_STEPS.md`.

For planning purposes this replaces options B (poll) and C (shared volume in production).

### 8.3 Recommended integration patterns (for the core)

**A — Asynchronous post-upload (aligned with 202 + job_id)** — **official SolidField pattern**
1. The client or Django stores `WorkOrderPhoto` (original file or a temporary URL).
2. If `add_watermark`, a Django service (signal, Celery, or a dedicated service) **POSTs** to the webhook with `image_url` pointing at a URL the worker can read (**signed**, short TTL, or an internal network with an SSRF rule on the worker).
3. Django persists `job_id` and a “watermark pending” state.
4. **Current gap:** Go only writes to `OUTPUT_DIR`. **SolidField decision (§8.2.1):** implement **upload to object storage (S3/MinIO)** + a **completion webhook** to Django; poll and shared volume stay off the official path.

**B — Synchronous in the core (not the current Go design)**
The Go service was designed for **202 + queue**; a synchronous flow would need another endpoint or a product change.

**C — Direct publish to the NATS queue from Django**
Possible in theory (a message equal to `JobMessage`), but it duplicates validation logic and exposes NATS to the core; normally **HTTP to the microservice** keeps a clearer boundary.

### 8.4 Checklist / industrial fishing

The product briefing asks for a binding of **WorkOrder + checklist + item**. **Filehub** still has no FK to checklist; until then, `work_reference` + `photo_context` / `description` can carry human-readable references. When FKs or an `evidence_code` exist, **solidfield_core** can map those fields to `photo_context` / new fields in the JSON (a contract extension on both sides).

---

## 9. Logical diagram: SolidField + watermarker

```
┌─────────────────────────────────────────────────────────────┐
│                    solidfield_core (Django)                  │
│  ┌──────────┐   ┌─────────────┐   ┌──────────────────────┐  │
│  │ orders   │   │ filehub     │   │ apis / checklist     │  │
│  │ WorkOrder│◄──│ WorkOrder   │◄──│ upload metadata      │  │
│  │          │   │ Photo       │   │                      │  │
│  └──────────┘   └──────┬──────┘   └──────────────────────┘  │
│                        │                                      │
│            (integration to implement)                         │
│                        │ POST webhook + X-Tenant-ID           │
└────────────────────────┼──────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              sf-watermarker-worker-go                         │
│   Gin ──► JetStream ──► Worker ──► final JPEG               │
└─────────────────────────────────────────────────────────────┘
                         │
        SolidField target: S3/MinIO + webhook ──► Django (Filehub)
        (in the Go code today: still local OUTPUT_DIR; see §8.2.1)
```

---

## 10. Environment variables (reference)

| Variable | Function |
|----------|----------|
| `OUTPUT_DIR` | Where to write `{job_id}.jpg` |
| `PORT` | HTTP port (default 8080) |
| `MAX_DIM` | Max longer side after resize |
| `GIN_MODE` | For example `release` |
| `NATS_*` | See section 6 |
| `ALLOW_PRIVATE_IPS` | `true` for dev only (SSRF) |

---

## 11. Related documentation in this repository

- **`README.md`** — how to run NATS, build with/without HEIF, `curl` examples.
- **`FILEHUB_WATERMARKER_NEXT_STEPS.md`** — Django guide + object-storage and webhook decision.
- **`FILEHUB_FISHING_MVP_BRIEFING.md`** — Filehub / fishing MVP briefing.

---

## 12. Executive summary

| Question | Answer |
|----------|--------|
| What is it? | A Go microservice: webhook → NATS queue → worker → JPEG on disk. |
| What is it for? | Watermark and field metadata without overloading Django. |
| Does it connect to Filehub? | **Semantically yes** (equivalent fields); **technically not yet** in the core code — orchestration, persistence of `job_id`, and **delivery of the final file** back to SolidField storage are still missing. |
| What should the core do next? | **Flow A adopted:** implement the Django webhook + a worker extension for **S3 + callback**; a mutual security contract; update `WorkOrderPhoto` idempotently. |

---

*Document kept alongside the **sf-watermarker-worker-go** code. Update it when a real integration exists in **solidfield_core** (code paths, new fields, callbacks).*
