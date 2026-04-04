# Documentação — Transformação SolidField para Pesca Industrial de Larga Escala

Este documento consolida **o que já existe no repositório**, **o que está em curso** e **a linha de produto** para um sistema voltado a **armadores / frotas industriais** (cenário tipo hub de Itajaí/SC), reutilizando o backend Django existente com **mínima dependência de UI web** no MVP (APIs + export + app cliente quando existir).

---

## 1. Objetivo da transformação

Transformar o SolidField de **SaaS genérico de operações em campo** em um **pacote enxuto** focado no **diário operacional em alto mar**:

- **Diesel** (consumo, abastecimento, estimativa em bordo)
- **Gelo** (massa estimada)
- **Temperatura da câmara / poço**
- **Turno / período** e **observações** no escopo operacional

Com **vínculo explícito à viagem** (`WorkOrder` como contêiner lógico), **estado de preenchimento e submissão**, **sincronização offline** quando não houver rede, e **saída tabular** para BI (Excel, Sheets, Power BI).

Isso ataca **OPEX imediato** (combustível, perecível) e prepara terreno para **Mapa de Bordo** e relatórios regulatórios numa fase seguinte — sem confundir o MVP com **quinhão** (motor societário que ainda **não existe** no código).

---

## 2. Visão de arquitetura (MVP)

```
┌─────────────────┐     HTTPS (quando houver rede)      ┌──────────────────────────┐
│  App de campo   │ ──────────────────────────────────► │  Django / DRF (SolidField)│
│  (Capacitor+    │   checklist, work orders, fila sync │  multi-tenant, RBAC       │
│   Vue+Ionic)*   │ ◄────────────────────────────────── │                           │
└────────┬────────┘                                     └────────────┬─────────────┘
         │                                                          │
         │ SQLite/IndexedDB local                                   │ Postgres
         │ (mutações enfileiradas)                                  │ WorkOrder, Checklist,
         └──────────────────────────────────────────────────────────► OfflineSyncQueue, …
```

\* **Frontend dedicado ainda não está neste repositório**; a orientação e o contrato de sync estão documentados em `backend/apps/core/` (ver secção 7).

Papel do backend neste MVP:

- **Fonte de verdade** após sync
- **Fila de mutações** (`OfflineSyncQueue`) para aplicar lote de respostas e submit idempotente
- **Export CSV** agregando respostas por viagem / tipo de serviço

---

## 3. O que já existe (implementado)

### 3.1 Domínio checklist + template pesca industrial

| Entrega | Descrição | Onde |
|--------|-----------|------|
| Template versionado v1 | 7 itens: turno (texto), diesel (L × 3), gelo (kg), temperatura (°C), observações | `backend/apps/checklist/defaults/pesca_diario_operacional.py` |
| Constantes de produto | Nome: `Diário Operacional — Pesca Industrial`; `service_type`: `pesca_industrial_diario` | Mesmo ficheiro |
| Seed idempotente | Comando Django por tenant / técnico | `backend/apps/checklist/management/commands/seed_pesca_diario_operacional.py` |
| Tipos numéricos | `volume_l`, `weight_kg`, `temperature` alinhados a codecs comuns | `backend.common.number_codecs` (referenciado no defaults) |

Documentação de apoio:

- `backend/apps/checklist/CHECKLIST_SCHEMA.md` — entidades, fluxos, invariantes, APIs
- `backend/apps/checklist/CHECKLIST_FORMULARIOS_NUMERICOS_E_PESCA.md` — formulários versionados e ligação aos codecs

### 3.2 Checklist ↔ viagem (`WorkOrder`)

- Criação de checklist com **`work_order`** opcional e **`filled_by`** opcional
- Validação de **tenant** alinhado (template, OS, técnico)
- Serviço e API atualizados (`checklist_service.py`, `checklist_api.py`)

### 3.3 Ciclo de vida e progresso

- Campo **`Checklist.status`**: `draft` | `submitted` (migration `0004_checklist_status`)
- **`submit_checklist`** define `submitted` e **`incomplete=False`** quando aplicável
- Serializers expõem **`status`** e **`incomplete`**
- APIs: progresso, listagem, detalhe, remoção de resposta (ver URLs)

### 3.4 Respostas em lote

- Endpoint **`POST .../create_checklist_item_answer_api/`** usa **`bulk_save_answers`** com `technician_operating` (correção de permissão aplicada no serviço)

### 3.5 Export para análise (BI / Excel)

- **`GET .../export_checklist_answers_csv_api/`** com filtros opcionais: `work_order_id`, `service_type` (ex.: `pesca_industrial_diario`), `template_id`
- UTF-8 **com BOM** para Excel
- Implementação: `backend/apps/checklist/services/checklist_export_service.py`

### 3.6 Fila offline

| Entrega | Descrição | Onde |
|--------|-----------|------|
| Modelo | `OfflineSyncQueue` com `pending` / `conflict` / `success`, `payload` JSON | `backend/apps/core/models/sync.py` |
| Idempotência | `client_mutation_id` único por técnico (quando preenchido) | Migration `core.0004_offlinesyncqueue_client_mutation` |
| Serviço | Enfileirar, listar, processar com lock; ações `checklist_batch_answers`, `checklist_submit` | `backend/apps/core/services/offline_sync_service.py` |
| APIs | `enqueue_offline_sync_api/`, `list_offline_sync_api/`, `process_offline_sync_api/<queue_id>/` | `backend/apps/core/api/offline_sync_api.py` + `apis/urls.py` |
| Permissões | `enqueue_offline_sync`, `process_offline_sync` | `backend/common/schemas/permission_schemas.py` |
| Testes | Serviço offline | `backend/apps/core/tests/test_offline_sync_service.py` |

Documentação: `backend/apps/core/OFFLINE_SYNC_QUEUE.md`, `CLIENT_OFFLINE_LOCAL_SYNC_ESQUEMA.md`, `CAPACITOR_VUE_IONIC_OFFLINE_SYNC.md`

### 3.7 Work orders (viagem / OS)

APIs registadas em `backend/apps/apis/urls.py`: criar, listar, obter, atualizar, atribuir, histórico de status, link de download (último conforme produto legado SolidField).

### 3.8 Contrato público da API (OpenAPI)

- **Swagger UI:** `GET /api/docs/`
- **Schema:** `GET /api/schema/`
- Configuração: `backend/config/urls.py`, `drf_spectacular`, `SPECTACULAR_SETTINGS` em `backend/config/settings.py`
- Tags e `operation_id` estáveis (prefixo `publicV1…`) para checklist, work orders, offline sync
- Política documentada: `API_PUBLIC_CONTRACT.md`

### 3.9 Outros ativos SolidField reutilizáveis (não exclusivos de pesca)

- **`filehub`:** fotos / assinaturas com geo — útil para evidência de medidor ou câmara (**integração por item ainda não fechada no fluxo pesca**)
- **`reporting`:** base para PDF/relatórios — **layout regulatório oficial** não tratado como concluído no MVP
- **RBAC / multi-tenant / auditoria:** núcleo `core` — sustentam o produto vertical

Visão macro de motores: `MICROSAAS_HEADLESS_AUDIT.md`

---

## 4. Rotas HTTP principais (prefixo `/api/`)

Definição central: `backend/apps/apis/urls.py`.

**Offline sync**

- `POST enqueue_offline_sync_api/`
- `GET list_offline_sync_api/`
- `POST process_offline_sync_api/<int:queue_id>/`

**Checklist (MVP pesca)**

- `POST create_checklist_api/` — body: `template`, opcional `work_order`, `filled_by`
- `POST create_checklist_item_answer_api/` — respostas em lote
- `DELETE remove_checklist_answer_api/<checklist_id>/<item_template_id>/`
- `GET list_checklists_api/`
- `GET get_checklist_api/<checklist_id>/`
- `POST submit_checklist_api/<checklist_id>/`
- `GET get_checklist_progress_api/<checklist_id>/`
- `GET export_checklist_answers_csv_api/`

**Templates** (administração / configuração do tenant)

- `create_checklist_template_api/`, `create_checklist_item_template_api/`, delegação a agrupamentos, versão de template, etc.

**Work orders**

- `create_work_order_api/`, `list_work_orders_api/`, `get_work_order_api/<id>/`, `update_work_order_api/<id>/`, `assign_work_order_api/<id>/`, `get_work_order_status_history_api/<id>/`, `create_work_order_download_link_api/`

Autenticação e formato de erro seguem o padrão DRF do projeto (ver `API_PUBLIC_CONTRACT.md` e schema OpenAPI).

---

## 5. Ordem operacional recomendada (backend)

1. `python manage.py migrate`
2. `python manage.py seed_pesca_diario_operacional --tenant-id <id> --technician-id <id>` (ou equivalente sem flags conforme doc do comando)
3. Criar/usar **`WorkOrder`** no mesmo tenant
4. `POST /api/create_checklist_api/` com `template` + `work_order`
5. Gravar respostas: **direto** via `create_checklist_item_answer_api` ou **offline** via `enqueue_offline_sync_api` + `process_offline_sync_api`
6. `POST /api/submit_checklist_api/<id>/` quando o diário estiver completo
7. `GET /api/export_checklist_answers_csv_api/?service_type=pesca_industrial_diario&work_order_id=...` para análise externa

Detalhes e histórico de alterações: `HISTORICO_IMPLEMENTACAO_CHECKLIST_PESCA.md`

---

## 6. Estratégia de produto (contexto Itajaí / industrial)

Documento de referência: `MICROSAAS_PESCA_INDUSTRIAL_ITAJAI.md`

Resumo:

- **Prioridade MVP:** diesel + gelo + temperatura (impacto direto em caixa)
- **Mapa de bordo:** mesmo motor de checklist + auditoria; camada legal/PDF em fase seguinte
- **Quinhão:** fora do núcleo atual; exige domínio novo (captura, preço, regras societárias)

---

## 7. Em que estamos a trabalhar / próximos incrementos

Estes itens são **planeamento explícito** ou **gaps** reconhecidos no código/docs:

| Área | Estado |
|------|--------|
| Congelar e comunicar contrato HTTP (`operation_id`, erros 422) | Em curso / parcialmente coberto pelo OpenAPI Public v1 |
| App Capacitor + Vue + Ionic (UI + armazenamento local + sync) | **Não está neste repo**; documentação de desenho em `CAPACITOR_VUE_IONIC_OFFLINE_SYNC.md` e `CLIENT_OFFLINE_LOCAL_SYNC_ESQUEMA.md` |
| Evidência fotográfica por item (medidor/câmara) via `filehub` | **Não integrado** de ponta a ponta ao fluxo do diário pesca |
| Mapa de bordo conforme normas específicas (PDF/validação com órgão) | **Não implementado** como produto regulatório |
| Motor de quinhão | **Inexistente** no repositório |
| Dashboard ou agendamento de relatórios | MVP assume **CSV + consumidores externos** |
| Telemetria automática (CAN, sensores) | **Fora de escopo** do checklist atual |

---

## 8. Limitações e compliance

- Regras de **pesca, segurança e documentação obrigatória** devem ser validadas com **especialistas e órgãos competentes**. Este software fornece **registro estruturado e rastreabilidade técnica**, não substitui assessoria jurídica ou homologação de formatos oficiais.
- O repositório não inclui ainda **SPA de produção** para o vertical; o foco implementado é **API + dados + sync**.

---

## 9. Índice de documentação relacionada

| Documento | Conteúdo |
|-----------|----------|
| `MICROSAAS_PESCA_INDUSTRIAL_ITAJAI.md` | Estratégia, dores do setor, MVP 30 dias, encaixe nos módulos |
| `HISTORICO_IMPLEMENTACAO_CHECKLIST_PESCA.md` | Cronologia técnica do que foi implementado e corrigido |
| `MICROSAAS_HEADLESS_AUDIT.md` | Inventário de motores reaproveisáveis (work orders, RBAC, sync, checklist) |
| `API_PUBLIC_CONTRACT.md` | Política de versão OpenAPI e lista resumida de rotas estáveis |
| `backend/apps/checklist/CHECKLIST_SCHEMA.md` | Schema declarativo do domínio checklist |
| `backend/apps/checklist/CHECKLIST_FORMULARIOS_NUMERICOS_E_PESCA.md` | Tipos numéricos e itens do diário |
| `backend/apps/core/OFFLINE_SYNC_QUEUE.md` | Contrato da fila e payloads |
| `backend/apps/core/CLIENT_OFFLINE_LOCAL_SYNC_ESQUEMA.md` | Cliente local / estados de sync |
| `backend/apps/core/CAPACITOR_VUE_IONIC_OFFLINE_SYNC.md` | Diretrizes app híbrido |

---

*Última consolidação: documentação alinhada ao estado do repositório **solidfield_core** para o vertical **pesca industrial de larga escala**.*
