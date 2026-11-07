# Versioned forms, numeric types, and the industrial-fishing daily log (diesel / ice / cold room)

This document explains **what the `checklist` app already provides** for *“versioned forms + numeric types (volume, temperature, and so on)”* and how that was **applied to the industrial-fishing scenario**: **diesel**, **ice**, **cold-room temperature** readings, and **per-shift/per-day records**.

Related documents:

- `CHECKLIST_SCHEMA.md` — domain model, services, and APIs in general.
- `defaults/pesca_diario_operacional.py` — canonical definition of the fishing template items.
- `FISHING_CHECKLIST_IMPLEMENTATION_HISTORY.md` (repository root) — timeline of what was implemented and changed in the project.

---

## 1. Where this lives in the code

| Concept | Where |
|---------|-------|
| Versioned template (name + version per tenant) | `models/checklist.py` — `ChecklistTemplate` (`unique_together`: tenant, name, version) |
| Form items (question, type, required flag, order) | `ChecklistItemTemplate` — `answer_type` field (choices in `FIELD_TYPE`) |
| Answer validation and type → stored-column mapping | `utils/checklist_util.py` — `expected_field_for_type`, `has_required_value` |
| Numeric types with unit / parsing (for example L, kg, °C) | `backend/common/number_codecs.py` — `NUMERIC_CODECS` |
| Execution (filled instance) | `Checklist` + `ChecklistItemAnswer` |
| Predefined fishing template | `defaults/pesca_diario_operacional.py` |
| Apply template v1 in the database | `management/commands/seed_pesca_diario_operacional.py` |

---

## 2. Versioned forms (what that means in practice)

- A **`ChecklistTemplate`** is the form “mold”: it has `name`, `version`, `service_type`, tenant, `is_active`, global or group scope (`aggroupments`), and so on.
- Several versions coexist under the **same name** as long as the **version** differs (for example v1, v2 after `update_checklist_template_version`).
- **`ChecklistItemTemplate`** rows are the form lines, with **`order`** fixing the sequence (shift first, then measurements, and so on).
- Each field completion creates a **`Checklist`** (instance) bound to a template **frozen at that version** and optionally to a **`WorkOrder`** (voyage).
  So “per-shift/per-day record” means **one `Checklist` per shift** (or per operational window), not a new template every day.

---

## 3. Numeric types (volume, temperature, mass, and so on)

### 3.1 Types declared on the item (`answer_type`)

On `ChecklistItemTemplate`, `answer_type` uses the `FIELD_TYPE` choices (the slice relevant to the fishing MVP):

- **Volume** measure: `volume_l` (liters), among others (for example `volume_gal`).
- **Mass** measure: `weight_kg` (kilograms), among others.
- **Temperature**: `temperature` (°C on the question; storage/validation aligned with the codec).

There is also a generic `number` and dozens of industrial types (electrical, dimensions, and so on) for other use cases.

### 3.2 Consistency with `NUMERIC_CODECS`

For the **`save_answer`** flow to work uniformly, “specialized numeric” types used on questions must exist in **`NUMERIC_CODECS`** (`number_codecs.py`). That guarantees:

- parsing that accepts a decimal comma (pt-BR) where applicable;
- the value persisted consistently in the **`answer_number`** field of `ChecklistItemAnswer` (via `expected_field_for_type` → `"answer_number"`).

The fishing template uses these explicitly:

- `volume_l` → liters (diesel);
- `weight_kg` → kilograms (ice);
- `temperature` → °C (cold room / hold).

### 3.3 Type → stored column summary

| `answer_type` (example) | Primary field on the answer |
|-------------------------|-----------------------------|
| `text` | `answer_texto` |
| `bool` | `answer_bool` |
| `choice` | `answer_choice` |
| `volume_l`, `weight_kg`, `temperature`, `number`, … | `answer_number` |

---

## 4. Application to the fishing MVP: diesel, ice, temperature, shift

**`defaults/pesca_diario_operacional.py`** defines the template **`Daily Operational Log — Industrial Fishing`** with `service_type = pesca_industrial_diario` and the items below.

| Order | Operational purpose | `answer_type` | Required |
|------:|---------------------|---------------|----------|
| 1 | **Shift** identification (date + period, for example morning) | `text` | Yes |
| 2 | Diesel **consumption** in the period (L) | `volume_l` | Yes |
| 3 | Diesel **refueling** in the period (L); 0 if none | `volume_l` | Yes |
| 4 | **Estimate** of total diesel on board after the period (L) | `volume_l` | No |
| 5 | **Ice** on board — estimated weight (kg) | `weight_kg` | Yes |
| 6 | Cold-room / hold **temperature** (°C) | `temperature` | Yes |
| 7 | Notes limited to the diesel / ice / cold-room scope | `text` | No |

The product-table line you cited is covered:

> Versioned forms + numeric types (volume, temperature, and so on) in `backend/apps/checklist/` for **diesel**, **ice**, **cold-room temperature** readings, and **per-shift/per-day records**.

- **Shift/day**: item 1 (text) + one **`Checklist` instance per completion** (ideally tied to the voyage **`WorkOrder`** — see the APIs in the project history).
- **Diesel / ice / temperature**: items 2–6 with types aligned to `NUMERIC_CODECS`.

To **create template v1** in a tenant database, use:

```bash
python manage.py seed_pesca_diario_operacional --tenant-id <id> --technician-id <id>
```

---

## 5. Versioning after v1

New versions of the same template name can be created by the **`update_checklist_template_version`** service (copies items, applies removals/additions, deactivates the previous version according to the parameters).
The seed documented here pins **v1 only** and is idempotent; form evolution (new operational or compliance fields) lands as **v2, v3, …** without losing the history of `Checklist` rows already bound to v1.

---

## 6. Known limitations

- Not every `answer_type` listed in `FIELD_TYPE` is in `NUMERIC_CODECS`; for new numeric items, validate in `checklist_util` / tests before production use.
- Free-text notes (item 7) depend on operational discipline; stricter semantic rules are described in `CHECKLIST_SCHEMA.md` (text-quality section).
