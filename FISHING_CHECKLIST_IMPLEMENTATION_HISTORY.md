# Histórico de implementação — Checklist + MVP Pesca industrial (SolidField)

Este documento resume **o que foi feito antes** (documentação, seed, estratégia) e **o que foi feito na continuação** (vínculo com viagem, status, export CSV, correções de API/serviço), no contexto do SolidField como SaaS de operações em campo.

---

## 1. Contexto

Objetivo de produto: usar o app **`checklist`** como base para um MVP de **diário operacional** (diesel, gelo, temperatura da câmara) para **pesca industrial**, com baixa dependência de UI e dados prontos para análise (BI/planilha).

O backend já tinha modelos e serviços de checklist; faltavam padronização documental, template de domínio, amarração explícita à **ordem de serviço / viagem** (`WorkOrder`) e uma saída tabular simples.

---

## 2. Trabalho feito anteriormente

### 2.1 Auditoria e produto (documentos na raiz do repositório)

- **`MICROSAAS_HEADLESS_AUDIT.md`** — Auditoria técnica dos motores reaproveitáveis do SolidField (work orders, RBAC de técnicos, sync offline, checklist, evidência geo, reporting), com visão de Micro-SaaS / APIs headless.

### 2.2 Estratégia pesca industrial (Itajaí)

- **`MICROSAAS_PESCA_INDUSTRIAL_ITAJAI.md`** — Mapeamento das dores do setor (diesel, gelo, mapa de bordo, quinhão) para módulos existentes; recomendação de MVP em ~30 dias; evolução do doc com seção de **implementação** (seed, API, export).

### 2.3 Esquematização do domínio `checklist/`

- **`backend/apps/checklist/CHECKLIST_SCHEMA.md`** — Visão declarativa: entidades, fluxo template → execução → submit, contratos de `answer_type`, APIs, invariantes.
- Inclusão de regras de **qualidade semântica** para geração/preenchimento de itens (não misturar **aquisição** e **contratação**; observações ligadas ao objeto do item; fluidez textual).

### 2.3.1 Formulários versionados + tipos numéricos (diesel, gelo, temperatura, turno)

- **`backend/apps/checklist/CHECKLIST_FORMULARIOS_NUMERICOS_E_PESCA.md`** — Documenta a parte que estava resumida na tabela de produto: como `ChecklistTemplate` / `ChecklistItemTemplate` versionam o formulário, como `volume_l`, `weight_kg`, `temperature` se conectam a `NUMERIC_CODECS` e `answer_number`, e a tabela dos 7 itens do diário pesca (registro por turno/dia).

### 2.4 Template “Diário operacional — pesca” (seed)

- **`backend/apps/checklist/defaults/pesca_diario_operacional.py`** — Constantes `TEMPLATE_NAME`, `SERVICE_TYPE` (`pesca_industrial_diario`) e lista **`ITEM_SPECS`** com 7 itens: turno (texto), consumo/abastecimento/remanescente de diesel (litros), gelo (kg), temperatura da câmara (°C), observações no escopo operacional.
- Função **`ensure_pesca_diario_operacional_template`**: cria a **versão 1** do template por tenant de forma **idempotente** (se já existir, não duplica).
- **`backend/apps/checklist/management/commands/seed_pesca_diario_operacional.py`** — Comando Django para aplicar o seed (`--tenant-id`, `--technician-id`, `--dry-run`).

Comando típico:

```bash
python manage.py seed_pesca_diario_operacional --tenant-id 1 --technician-id 1
```

---

## 3. Trabalho feito na continuação (após “sim, pode continuar”)

### 3.1 Vínculo checklist ↔ viagem (`WorkOrder`)

- **`create_checklist`** (`checklist_service.py`) passou a aceitar **`work_order` opcional** e **`filled_by` opcional** (se `filled_by` não vier, usa o `technician_operating`).
- Validação de **tenant**: template, `work_order` e técnico preenchedor devem pertencer ao mesmo tenant do operador.
- **`create_checklist_api`**: resolve `template` e `work_order` com filtro por `tenant_id`; body pode incluir `filled_by`; retorna erros explícitos (`template_not_found`, `work_order_not_found`, etc.).

### 3.2 Ciclo de vida `draft` / `submitted`

- Campo **`Checklist.status`** (`draft` | `submitted`) adicionado ao modelo + migration **`0004_checklist_status`**.
- **`submit_checklist`**: ao submeter com sucesso, define `status=submitted` e **`incomplete=False`**.
- Serializers passam a expor também **`incomplete`** junto com `status`.

### 3.3 Correções de bugs e consistência

- **`create_checklist`**: corrigido uso de `errors` antes de declarar na falha de permissão.
- **`bulk_save_answers`**: passa **`technician_operating`** para **`save_answer`** (antes chamava sem operador e quebrava validação de permissão).
- **`remove_answer`**: em falha de permissão retorna **`False`** (antes retornava `None` de forma inconsistente com a assinatura).
- **`Checklist.__str__`**: não assume mais `work_order` sempre preenchido.
- **`ChecklistDetailSerializer`**: uso correto da relação **`answers`** (em vez de `checklistitemanswer_set`).
- **`checklist_template_api`**: import de **`next_order_for_template`** ajustado para **`checklist_template_util`** (antes importava incorretamente do service).

### 3.4 Export CSV para BI / Excel

- Novo módulo **`backend/apps/checklist/services/checklist_export_service.py`**: monta CSV com uma linha por resposta (e linha “vazia” de item quando o checklist não tem respostas), incluindo identificadores de viagem, template, técnico e colunas de resposta.
- Novo endpoint **`GET /export_checklist_answers_csv_api/`** (registrado em **`backend/apps/apis/urls.py`**), com filtros opcionais na query:
  - `work_order_id`
  - `service_type` (ex.: `pesca_industrial_diario`)
  - `template_id`  
  Arquivo em UTF-8 com **BOM** para abrir bem no Excel.

### 3.5 Documentação atualizada

- **`CHECKLIST_SCHEMA.md`** — Seção de atenções atualizada (itens resolvidos + gaps remanescentes); inclusão da rota de export.
- **`MICROSAAS_PESCA_INDUSTRIAL_ITAJAI.md`** — Seção 7.3 descrevendo vínculo com `WorkOrder` e export CSV; 7.4 com próximos passos opcionais.

### 3.6 Limpeza

- Removido arquivo solto **`command.txt`** dentro de `management/commands/` (comandos de exemplo duplicavam o que já está no doc de pesca).

### 3.7 Fila offline (`OfflineSyncQueue`)

- Modelo **`OfflineSyncQueue`**: campo **`client_mutation_id`** + *unique* parcial por técnico (idempotência); `related_name` **`offline_sync_items`**.
- Migration **`core/0004_offlinesyncqueue_client_mutation.py`**.
- Permissões **`enqueue_offline_sync`** e **`process_offline_sync`** em **`permission_schemas.py`** (L1 + herança L2/L3).
- Serviço **`core/services/offline_sync_service.py`**: enfileirar, listar fila do técnico, processar item com *lock* (`select_for_update`); ações **`checklist_batch_answers`** e **`checklist_submit`**; reprocessamento de **`conflict`**; **`success`** idempotente no processamento.
- APIs: **`enqueue_offline_sync_api`**, **`list_offline_sync_api`**, **`process_offline_sync_api/<queue_id>/`** em **`core/api/offline_sync_api.py`**, rotas em **`apis/urls.py`**.
- Doc **`backend/apps/core/OFFLINE_SYNC_QUEUE.md`**; testes básicos em **`core/tests/test_offline_sync_service.py`**.

---

## 4. Ordem recomendada de uso (operacional)

1. Rodar migrações: `python manage.py migrate` (app `checklist` para o campo `status`).
2. Seed do template de pesca por tenant: `seed_pesca_diario_operacional`.
3. Criar ou usar uma **`WorkOrder`** da viagem (mesmo tenant).
4. **`POST create_checklist_api/`** com `template` + `work_order`.
5. **`POST create_checklist_item_answer_api/`** para salvar respostas.
6. **`GET export_checklist_answers_csv_api/`** com filtros desejados para análise externa.

---

## 5. Arquivos principais (referência rápida)

| Área | Arquivos |
|------|-----------|
| Estratégia / auditoria | `MICROSAAS_HEADLESS_AUDIT.md`, `MICROSAAS_PESCA_INDUSTRIAL_ITAJAI.md` |
| Schema checklist | `backend/apps/checklist/CHECKLIST_SCHEMA.md` |
| Seed pesca | `backend/apps/checklist/defaults/pesca_diario_operacional.py`, `.../management/commands/seed_pesca_diario_operacional.py` |
| Serviço + API checklist | `backend/apps/checklist/services/checklist_service.py`, `.../api/checklist_api.py` |
| Export CSV | `backend/apps/checklist/services/checklist_export_service.py` |
| Modelo + migration status | `backend/apps/checklist/models/checklist.py`, `.../migrations/0004_checklist_status.py` |
| Fila offline | `backend/apps/core/models/sync.py`, `core/migrations/0004_offlinesyncqueue_client_mutation.py`, `core/services/offline_sync_service.py`, `core/api/offline_sync_api.py`, `OFFLINE_SYNC_QUEUE.md` |
| Rotas | `backend/apps/apis/urls.py` |

---

## 6. O que ainda não foi feito (fora deste histórico)

- Integração automática com **`filehub`** (foto de medidor/termômetro) por item.
- Motor de **quinhão** ou mapa de bordo **legal** completo (PDF regulatório específico).
- Telas frontend dedicadas; o MVP assume APIs + CSV + cliente HTTP/planilha.

Este arquivo é apenas **memória de implementação**; regras de negócio e compliance devem ser validadas com especialistas e órgãos competentes antes de uso em produção regulada.
