# SolidField

SolidField is a multi-tenant backend for field operations. A company (tenant) registers technicians, clients, and work orders. Technicians complete versioned checklists in the field, including while offline, and sync when the network is back. Photos, signatures, client feedback, and an audit log stay attached to the same tenant.

The HTTP API is the contract for a field app (Capacitor / Vue / Ionic). Interactive docs are served by the Django process.

## Stack

- Python 3.10+ and Django 5.2
- Django REST Framework with JWT (`djangorestframework-simplejwt`)
- PostgreSQL (`psycopg`)
- OpenAPI via `drf-spectacular`
- Object-level permissions (`django-guardian`), model history (`django-simple-history`), structured logs (`structlog`)

## Apps

Business rules live in each app’s `services/` and `utils/`. API views call those functions; they do not own the rules.

| App | Responsibility |
|-----|----------------|
| `core` | Tenants, account-holder users, technicians, L1/L2/L3 permissions, temporary delegation, audit log, offline sync queue |
| `orders` | Work orders, status history, per-tenant identifiers, download links |
| `checklist` | Templates, versioning, answers, submit/progress, CSV export. Includes a seed for the industrial-fishing daily log (diesel, ice, cold-room temperature) |
| `clients` | Clients, addresses, feedback links and ratings |
| `filehub` | Work-order photos and signatures |
| `apis` | URL mount for the HTTP API under `/api/` |
| `panel`, `reporting`, `quality_control`, `mobile_sync` | Registered apps. They currently contain only `apps.py` |

Permission levels on a technician:

- **L1** — field
- **L2** — local control
- **L3** — operational management

L3 can delegate selected actions to another technician for a time window.

Tenants can replace the default work-order status workflow with their own JSON definition.

## Layout

```
solidfield_core/
├── manage.py
├── requirements.txt
├── pytest.ini
├── backend/
│   ├── config/          # settings, root URLs, WSGI/ASGI
│   ├── common/          # shared validators, number codecs, error messages
│   ├── publisher.py     # signed HTTP publish to an optional Go service
│   └── apps/
└── API_PUBLIC_CONTRACT.md
```

## Setup

PostgreSQL must be running and reachable. From the repository root:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in the repository root. `backend/config/settings.py` reads it through `django-environ`:

```
POSTGRES_DB=solidfield
POSTGRES_USER=solidfield
POSTGRES_PASSWORD=solidfield
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Logging writes to `logs/json.log` and `logs/flat_line.log`. Create that directory before starting the server:

```bash
mkdir -p logs
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`createsuperuser` asks for **email**, not a username. `AccountHolderUser.email` is the login field.

Useful URLs once the server is up:

| URL | What it is |
|-----|------------|
| http://127.0.0.1:8000/admin/ | Django admin (Django JET is mounted at `/jet/`) |
| http://127.0.0.1:8000/api/docs/ | Swagger UI |
| http://127.0.0.1:8000/api/schema/ | OpenAPI schema |
| http://127.0.0.1:8000/token_api/tokenjwt/ | JWT obtain pair |
| http://127.0.0.1:8000/token_api/tokenjwt/refresh/ | JWT refresh |

API routes are under `/api/`. Authenticate with `Authorization: Bearer <access>`. The stable field-app surface is the **Public v1** tag; see [API_PUBLIC_CONTRACT.md](API_PUBLIC_CONTRACT.md).

Export the schema from the repo root:

```bash
python manage.py spectacular --file openapi.yaml
python manage.py spectacular --validate
```

Seed the industrial-fishing checklist for the first active tenant (pass `--dry-run` to preview):

```bash
python manage.py seed_pesca_diario_operacional --dry-run
python manage.py seed_pesca_diario_operacional --tenant-id 1 --technician-id 1
```

## Tests

`pytest.ini` points at `backend.config.settings`. The suite uses Django `TestCase`. `pytest` and `pytest-django` are not pinned in `requirements.txt`; install them if you want pytest:

```bash
pip install pytest pytest-django
pytest
pytest backend/apps/orders/tests/test_work_order_identifier_service.py
```

The same tests run through Django:

```bash
python manage.py test
python manage.py test backend.apps.checklist.tests.test_checklist
```

Tests need the same PostgreSQL `.env` as the app.

## Optional Go publisher

`backend/publisher.py` posts UI messages to a Go service. The body is JSON, signed with HMAC-SHA256 (`X-Signature: sha256=...`) and an `X-Idempotency-Key`. Defaults:

- `GO_PUBLISH_URL` — `http://localhost:8080/publish`
- `OUTBOUND_SIGNATURE_SECRET` — a placeholder byte string

Set both in Django settings before using this in anything other than local development. Delivery is meant to run after the database transaction commits.

## Further reading

| Document | Subject |
|----------|---------|
| [API_PUBLIC_CONTRACT.md](API_PUBLIC_CONTRACT.md) | What is stable in Public v1 |
| [backend/apps/checklist/README.md](backend/apps/checklist/README.md) | Checklist app |
| [backend/apps/checklist/CHECKLIST_SCHEMA.md](backend/apps/checklist/CHECKLIST_SCHEMA.md) | Template and answer schema |
| [backend/apps/checklist/CHECKLIST_NUMERIC_FORMS_AND_FISHING.md](backend/apps/checklist/CHECKLIST_NUMERIC_FORMS_AND_FISHING.md) | Numeric codecs and the fishing log |
| [backend/apps/core/OFFLINE_SYNC_QUEUE.md](backend/apps/core/OFFLINE_SYNC_QUEUE.md) | Offline mutation queue |
| [backend/apps/core/CLIENT_OFFLINE_LOCAL_SYNC_SCHEMA.md](backend/apps/core/CLIENT_OFFLINE_LOCAL_SYNC_SCHEMA.md) | Client-side sync schema |
| [backend/apps/core/CAPACITOR_VUE_IONIC_OFFLINE_SYNC.md](backend/apps/core/CAPACITOR_VUE_IONIC_OFFLINE_SYNC.md) | Field-app offline flow |
| [SF_WATERMARKER_SOLIDFIELD_INTEGRATION.md](SF_WATERMARKER_SOLIDFIELD_INTEGRATION.md) | Photo watermark worker integration |

## Development notes

`DEBUG` is on and `SECRET_KEY` in `backend/config/settings.py` is a development placeholder. Do not deploy this settings module as-is. `CORS_ALLOW_ALL_ORIGINS` is `True`. `ALLOWED_HOSTS` is empty, which is fine for `runserver` on localhost and wrong for a public host.
