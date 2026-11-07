# SolidField × Large-Scale Industrial Fishing (Itajaí/SC)

**Role:** Operations Engineer and Business Strategist — shipowner / industrial-fleet scenario in the Itajaí hub.

**Purpose of this document:** map SolidField’s current structure (real-time field-operations SaaS) onto an **entry Micro-SaaS (MVP)** that attacks the pain with the greatest immediate economic impact for the shipowner, with **low UI effort** and **high analytical value (IT)**.

For **consolidated technical documentation** (what already exists in code, routes, offline, OpenAPI, and roadmap), see **`LARGE_SCALE_INDUSTRIAL_FISHING_DOCUMENTATION.md`** at the repository root.

---

## 1. Reading SolidField for industrial fishing

The repository offers **reusable** capabilities (without assuming modules that do not exist in the code):

| Capability in code | Where it lives | Direct use in fishing |
|--------------------|----------------|------------------------|
| Versioned forms + numeric types (volume, temperature, and so on) | `backend/apps/checklist/` + seed in `checklist/defaults/pesca_diario_operacional.py` | **Diesel**, **ice**, **cold-room temperature** readings, per-shift/per-day records | done
| Field execution + progress + submission | `checklist/services/checklist_service.py` | Structured “daily log” with required-field rules before closing the day |
| Offline queue | `backend/apps/core/models/sync.py` (`OfflineSyncQueue`) | At sea with no signal: queue answers and sync at port |
| Evidence (photo/signature + geo) | `backend/apps/filehub/` | Proof of a reading, ice condition, seals, refueling receipt |
| Operational object per voyage | `backend/apps/orders/` (`WorkOrder`) | Logical container: **1 voyage / 1 at-sea batch** binding checklists and evidence |
| Audit + trail + permissions | `core` + logs | Less fraud and a stronger defense in inspections / internal disputes |
| Report / PDF output | `reporting` + download links in `orders` | Base for an **official vessel log (Mapa de Bordo)** or a package for the authority (depends on what `reporting` already generates today) |

**What is not ready as an isolatable engine in the current code:**

- Formal parts inventory / BOM / stock
- Automatic engine telemetry (CAN bus, sensors)
- **Catch-share engine** (payout rules by catch, crew, and shipowner)

That would be a new product or an integration — it does not block the MVP recommended below.

---

## 2. Critical sector variables × fit in SolidField

### 2.1 Volatile supplies — Diesel vs. range

- **Fit:** checklist with numeric fields + notes + (optional) panel/gauge photo (`filehub`).
- **Analytical value:** time series per voyage; simple rules (consumption/day vs. declared stock, heuristic alerts).
- **Cash impact:** diesel is often one of the largest OPEX items; planning error creates immediate cost (unsuitable time at sea, an extra port call, emergency purchase).

### 2.2 Perishable logistics — Ice, temperature vs. time at sea

- **Fit:** temperature types and measurements on the checklist + photographic evidence.
- **Cash impact:** lost product and wasted (“burned”) ice is direct money.

### 2.3 Legal compliance — Official vessel log (Mapa de Bordo) for regulators

- **Fit:** versioned template + submission + audit + export/PDF (if `reporting` covers it; otherwise the MVP is structured JSON + CSV, with PDF in a later phase).
- **Impact:** fines, detention, delay — a legal and operational drain at the port.

### 2.4 Catch-share calculation — Profit split (actual catch)

- **Current fit:** **there is no** core for this in the repository; it requires a catch model (weight, species, sold value) plus a rules engine.
- **Risk of a 30-day MVP:** high — disputes over rules and data quality; better as phase 2 after a trustworthy operational daily log.

---

## 3. One capability for ~30 days (Micro-SaaS MVP)

### 3.1 Single recommendation

**Working name:** *Operational Logbook — Diesel, Ice, and Cold Room* (commercial brand to be defined).

**Definition:** a **package of versioned templates + execution + offline sync**, bound to a **“Voyage”** (conceptually: `WorkOrder` as the voyage or at-sea cycle), with a **stable API and/or export** for BI/spreadsheet instead of a heavy UI at launch.

### 3.2 Why this, and not only the official vessel log or only the catch share

| Option | Pros | Cons for 30 days |
|--------|------|------------------|
| **Diesel + ice + cold room** | Fits checklist + offline; **immediate** savings on variable OPEX | Needs filling discipline (mitigated with evidence) |
| **Official vessel log only** | High regulatory value | The bottleneck is usually **legal layout + validation with the authority**, not software alone |
| **Catch share only** | High corporate value | New domain; catch/price data; shipowner/crew conflict |

**Explicit priority:** maximize **immediate cash savings** for the shipowner → **diesel + ice/temperature** first.

**Official vessel log (Mapa de Bordo)** as **phase 1b or 2:** the same engine (`checklist` + audit + reporting), a different template, and an official-document pipeline.

**Catch share** after there is a **trustworthy sold catch** (weight, species, value, deductions).

---

## 4. Lean 30-day scope

1. **Templates (versioned):** blocks for daily diesel refueling/consumption, ice (estimated stock or scale), cold-room temperature, operational notes — aligned with the semantic rules in `backend/apps/checklist/CHECKLIST_SCHEMA.md` (for example: do not mix acquisition and contracting in single-context items).
2. **Voyage context:** 1 `WorkOrder` = 1 voyage (or 1 at-sea cycle); checklists and evidence linked to it.
3. **Offline:** use `OfflineSyncQueue` for filling at sea.
4. **Analytical output (high IT, low UI):** endpoint or CSV export of answers aggregated by voyage/day — the shipowner uses Excel, Google Sheets, or Power BI in the MVP.
5. **Quick optional:** gauge/cold-room photo with geo (`filehub`) to reduce internal disputes.

---

## 5. Executive summary

| Criterion | Best fit in SolidField |
|-----------|------------------------|
| Pain that most affects short-term **operating cash** | **Diesel + ice/temperature** (the data fits the checklist) |
| **Regulatory** pain | **Official vessel log** (same engine; legal/PDF layer next) |
| **Corporate / profit** pain | **Catch share** (new domain — do not prioritize for a 30-day MVP) |

**Single 30-day MVP:** a Micro-SaaS for **structured operational recording (diesel, ice, cold room) with offline and analytics via API/export**, using `checklist` + `WorkOrder` (voyage) + `OfflineSyncQueue` (+ optional `filehub`) — maximum reuse of SolidField, minimal initial UI, maximum analytical return and direct impact on the shipowner’s cash.

---

## 6. Suggested next steps (outside the scope of this .md)

- Product one-pager: ICP (Itajaí shipowner / fleet manager), up to 3 screens, IT KPIs, and an explicit list of what **does not** enter the MVP.
- Stable OpenAPI for the checklist/execution endpoints used by the MVP.
- Validation with 1–2 shipowners on the minimum daily-log fields (diesel/ice/temperature) before freezing templates v1.

---

## 7. Implementation in the repository (first part — checklist template)

A **versioned v1 template** was added with items aligned to the MVP (diesel in liters, ice in kg, cold-room temperature in °C, shift as text, and notes restricted to the operational scope).

### 7.1 Where it is in the code

- Item definition and idempotent function: `backend/apps/checklist/defaults/pesca_diario_operacional.py`
- Django command (per tenant): `backend/apps/checklist/management/commands/seed_pesca_diario_operacional.py`

Useful constants:

- Template name: `Daily Operational Log — Industrial Fishing`
- `service_type`: `pesca_industrial_diario`

### 7.2 How to apply it

From the project root (with the venv active, if you use one):

```bash
cd /home/adryan/solidfield_core
python manage.py seed_pesca_diario_operacional --dry-run
python manage.py seed_pesca_diario_operacional --tenant-id 1 --technician-id 1
```

- If `--tenant-id` is omitted, the command uses the **first** active `CompanyTenant`.
- If `--technician-id` is omitted, it uses the **first** active `Technician` of that tenant (as the template `created_by`).
- If template **v1** with that name already exists for the tenant, the command **changes nothing** (idempotent).

### 7.3 Voyage link and export (implemented)

- **Create a checklist with a voyage:** `POST /create_checklist_api/` with JSON `template`, optional `work_order` (ID of a `WorkOrder` in the same tenant), optional `filled_by` (otherwise the session technician is used).
- **CSV export for BI:** `GET /export_checklist_answers_csv_api/` with optional query `work_order_id`, `service_type` (for example `pesca_industrial_diario`), `template_id`. Response: a CSV file (UTF-8 with BOM for Excel).

### 7.4 Next product step (optional)

- Optional: evidence items (`filehub`) for a gauge / thermometer photo.
- A dedicated dashboard or scheduled reports (today: manual CSV download).
