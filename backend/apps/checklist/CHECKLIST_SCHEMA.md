# Checklist Domain Schema (Declarative View)

## Scope

This file documents the `backend/apps/checklist/` domain in a declarative way:

- data model and relations
- service responsibilities
- runtime flow (template -> execution -> submit)
- API surface
- current implementation attention points

---

## 1) Domain map

### Main files

- `models/checklist.py`
- `services/checklist_template_service.py`
- `services/checklist_service.py`
- `utils/checklist_template_util.py`
- `utils/checklist_util.py`
- `api/checklist_api.py`
- `api/checklist_template_api.py`
- `api/serializers/checklist_serializers.py`

### Core dependencies outside app

- `core.models.technician.Technician`
- `core.models.technician.TechniciansAggroupment`
- `orders.models.WorkOrder`
- `core.services.technician_permission_service.has_permission`

---

## 2) Data schema (entity level)

## 2.1 ER view

```text
ChecklistTemplate (tenant-owned, soft-deletable)
  1 --- * ChecklistItemTemplate
  1 --- * Checklist
  * --- * TechniciansAggroupment (M2M)

Checklist
  1 --- * ChecklistItemAnswer
  * --- 1 Technician (filled_by)
  * --- 1 WorkOrder (optional)

ChecklistItemAnswer
  * --- 1 ChecklistItemTemplate
```

## 2.2 Entities and key fields

### `ChecklistTemplate`

- tenant-scoped (`unique_together`: tenant + name + version)
- key fields:
  - `name`
  - `version`
  - `service_type`
  - `is_active`
  - `is_global`
  - `created_by`
  - `aggroupments` (M2M)

### `ChecklistItemTemplate`

- belongs to one template
- ordered sequence (`order`)
- key fields:
  - `question`
  - `answer_type`
  - `required`
  - `choice_options`
- ordering: by `order`

### `Checklist`

- runtime instance of a template
- key fields:
  - `template`
  - `filled_by`
  - `work_order` (optional)
  - `incomplete`

### `ChecklistItemAnswer`

- one answer per (`checklist`, `item_template`) (`unique_together`)
- value model (single logical answer spread across typed columns):
  - `answer_bool`
  - `answer_texto`
  - `answer_number`
  - `answer_choice`
  - `note`

---

## 3) Answer type contract

Source: `models/checklist.py` + `utils/checklist_util.py`

### 3.1 Allowed `answer_type`

- basic: `bool`, `text`, `number`, `choice`
- numeric specialized:
  - angle: `degree`
  - metric dimensions: `length_cm`, `width_cm`, `height_cm`, `area_m2`, `volume_l`, `weight_kg`
  - imperial dimensions: `length_in`, `width_in`, `height_in`, `area_ft2`, `volume_gal`, `weight_lb`
  - electrical/energy: `voltage`, `current_amp`, `frequency_hz`, `power_w`, `power_kw`
  - environmental: `temperature`, `temperature_f`, `pressure`, `humidity_pct`, `speed_kmh`, `speed_mph`

### 3.2 Field mapping rule (`expected_field_for_type`)

- `bool` -> `answer_bool`
- `text` -> `answer_texto`
- `choice` -> `answer_choice`
- numeric types -> `answer_number`

### 3.3 Required validation rule (`has_required_value`)

- `bool`: must be explicit `True` or `False`
- `text`: non-empty string
- `choice`: non-empty string and must exist in `choice_options`
- numeric: int/float or non-empty numeric string

---

## 4) Service layer responsibilities

## 4.1 Template lifecycle (`checklist_template_service.py`)

- `create_checklist_template(...)`
  - permission gate: `create_checklist_template`
  - creates tenant-owned template

- `add_item_to_checklist_template(...)`
  - permission gate: `add_item_to_checklist_template`
  - resolves/validates `order` uniqueness
  - creates item with type + required + options

- `delegate_checklist_template_to_aggroupment(...)`
  - permission gate: `delegate_checklist_template_to_aggroupment`
  - when template is global, flips to non-global and binds first group
  - otherwise adds group relation

- `remove_aggroupment_from_template(...)`
  - permission gate: `remove_aggroupment_from_template`
  - prevents invalid state when removing the last group of a non-global template

- `update_checklist_template_version(...)`
  - permission gate: `update_checklist_template_version`
  - creates next version
  - copies previous items (bulk)
  - can remove items by order
  - can add new items
  - can copy aggroupments
  - can deactivate previous version

## 4.2 Execution lifecycle (`checklist_service.py`)

- `create_checklist(...)`
  - permission gate: `submit_checklist`
  - creates checklist runtime instance

- `save_answer(...)`
  - permission gate: `save_answer`
  - maps value to typed column
  - validates required and choice membership
  - upsert behavior (`get_or_create`)

- `bulk_save_answers(...)`
  - loops payload list and delegates to `save_answer`
  - accumulates partial errors

- `remove_answer(...)`
  - permission gate: `remove_answer`
  - deletes answer for item within checklist

- `list_missing_required_answers(...)`
  - scans required item templates and compares with stored answers
  - returns missing item IDs

- `submit_checklist(...)`
  - permission gate: `submit_checklist`
  - blocks if required answers are missing
  - marks checklist as submitted (status field expected)

- `get_checklist_progress(...)`
  - computes:
    - total items
    - required items
    - answered items
    - missing required count
    - percentages
    - answer details payload

---

## 5) Runtime flow (happy path)

```text
1) Create Template
   POST create_checklist_template_api

2) Add Template Items
   POST create_checklist_item_template_api
   (repeat per question; or use version update with items_to_add)

3) (Optional) Scope Template by Group
   POST delegate_checklist_template_to_aggroupment_api

4) Start Checklist Execution
   POST create_checklist_api (template + optional work_order)

5) Save Answers
   POST create_checklist_item_answer_api (batch)

6) Check Progress
   GET get_checklist_progress_api/<checklist_id>

7) Submit
   POST submit_checklist_api/<checklist_id>
   (blocked if required answers missing)
```

---

## 6) API surface (`backend/apps/apis/urls.py`)

### Execution APIs

- `POST /create_checklist_api/`
- `POST /create_checklist_item_answer_api/`
- `DELETE /remove_checklist_answer_api/<checklist_id>/<item_template_id>/`
- `GET /list_checklists_api/`
- `GET /get_checklist_api/<checklist_id>/`
- `POST /submit_checklist_api/<checklist_id>/`
- `GET /get_checklist_progress_api/<checklist_id>/`
- `GET /export_checklist_answers_csv_api/` (query: `work_order_id`, `service_type`, `template_id`)

### Template APIs

- `POST /create_checklist_template_api/`
- `POST /create_checklist_item_template_api/`
- `GET /get_next_order_for_template_api/<template_id>/`
- `POST /delegate_checklist_template_to_aggroupment_api/<template_id>/`
- `DELETE /remove_aggroupment_from_template_api/<template_id>/<aggroupment_id>/`
- `POST /update_checklist_template_version_api/<template_id>/`

---

## 7) Serialization contract (read APIs)

Source: `api/serializers/checklist_serializers.py`

- checklist list/detail includes:
  - template snapshot (`ChecklistTemplateSerializer`)
  - `filled_by` technician payload
  - `work_order_id` and `work_order_identifier`
  - `status`, timestamps
- detail includes answer list with:
  - item metadata (`question`, `answer_type`, `required`)
  - typed answer fields + note

---

## 8) Business invariants

- template version uniqueness per tenant/name
- item order uniqueness inside template
- single answer per checklist item template
- required answers must be present before submit
- permission gates are enforced in service layer per action

---

## 9) Attention points in current implementation

Resolved / updated in codebase:

- `create_checklist(...)` accepts optional `work_order` and optional `filled_by` (defaults to `technician_operating`); API validates tenant scope.
- `bulk_save_answers(...)` passes `technician_operating` into `save_answer(...)`.
- `Checklist.status` exists (`draft` | `submitted`) with migration `0004_checklist_status`.
- `Checklist.__str__` handles missing `work_order`.
- `ChecklistDetailSerializer` uses default `answers` relation (`related_name="answers"`).

Remaining gaps (optional follow-ups):

- `create_checklist_template_api` pode não alinhar todos os parâmetros exigidos por `create_checklist_template` (ex.: `technician` criador, `is_global`); revisar ao evoluir o app.

---

## 10) Suggested extraction boundaries (if checklist becomes headless module)

- Keep inside module:
  - template model + versioning
  - item schema and answer validation
  - execution lifecycle and progress computation

- Isolate via adapters:
  - technician/auth provider
  - work order provider
  - audit/event publisher

- Public contracts to freeze first:
  - template CRUD/version schema
  - batch answer payload schema
  - progress/submit response schema

---

## 11) Regras de qualidade para geracao de objeto (Checklist Item)

Esta secao define guardrails para evitar erros semanticos na geracao de objetos, descricoes ou observacoes por item.

### 11.1 Separacao obrigatoria de dominio

- **Nao misturar `aquisicao` com `contratacao`**.
- `aquisicao`: compra/entrada de material, item fisico, estoque, recebimento, consumo.
- `contratacao`: servico, mao de obra, fornecedor contratado, escopo contratual.
- Se o item for de aquisicao, toda a descricao, validacao e observacao devem permanecer no contexto de aquisicao.
- Se o item for de contratacao, toda a descricao, validacao e observacao devem permanecer no contexto de contratacao.

### 11.2 Regra de contexto por item

- Toda observacao deve referenciar diretamente o item atual (objeto, atributo ou condicao do proprio item).
- E proibido adicionar observacao generica ou paralela sem relacao com o item.
- Exemplo de erro: item sobre "aquisicao de seringa" com observacao sobre processo de contratacao.
- Exemplo correto: item sobre "aquisicao de seringa" com observacao sobre quantidade, lote, validade, fornecedor do material ou conformidade de recebimento.

### 11.3 Fluidez e coerencia textual

- Estrutura recomendada por item:
  1) objeto
  2) acao/verificacao
  3) criterio esperado
  4) observacao contextual (quando aplicavel)
- Evitar mudanca de assunto dentro da mesma frase.
- Evitar termos vagos ("coisas fora do padrao") sem declarar qual padrao foi violado.

### 11.4 Checklist de validacao semantica (antes de salvar/emitir)

- O item pertence a `aquisicao` ou `contratacao`?
- Existe qualquer termo do outro dominio misturado no texto?
- A observacao cita o mesmo objeto do item?
- O criterio de conformidade esta claro e mensuravel?
- O texto final esta fluido (sem quebra de contexto)?

### 11.5 Recomendacao tecnica de implementacao

- Incluir um campo explicito de classificacao no item/template, por exemplo:
  - `domain_scope`: `aquisicao` | `contratacao`
- Aplicar validacao de consistencia semantica:
  - bloquear termos conflitantes entre escopos
  - exigir observacao contextual por regra (`item_keyword overlap`)
- Em fluxos com IA/geracao de texto, usar prompt guardrails:
  - "nao misture aquisicao e contratacao"
  - "observacao obrigatoriamente ligada ao objeto do item"

