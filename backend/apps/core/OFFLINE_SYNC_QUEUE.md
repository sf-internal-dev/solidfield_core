# Fila de sincronização offline (`OfflineSyncQueue`)

Para **gravação só no aparelho** e só depois `enqueue` + `process`, ver o roteiro do cliente em **`CLIENT_OFFLINE_LOCAL_SYNC_ESQUEMA.md`** (estados, campos sugeridos no SQLite/IndexedDB, diagrama e pseudo-código de sync).

## Modelo

- `technician`: dono da fila (normalmente o técnico do dispositivo).
- `status`: `pending` | `conflict` | `success`.
- `payload`: JSON com a mutação (ver contrato abaixo).
- `client_mutation_id`: opcional, para **idempotência** (ex.: UUID gerado no app); único por técnico quando preenchido.
- `synced_at`: preenchido ao aplicar com sucesso.

Migração: `core.0004_offlinesyncqueue_client_mutation`.

## Permissões (schema)

- `enqueue_offline_sync` — enfileirar e listar a própria fila.
- `process_offline_sync` — processar itens pendentes (ou re-tentar `conflict`).

Herdadas em L1; L2 e L3 incluem essas ações via herança seletiva no `permission_schemas`.

## APIs (`backend/apps/apis/urls.py`)

| Método | Caminho | Uso |
|--------|---------|-----|
| POST | `enqueue_offline_sync_api/` | Corpo: `payload` (objeto), opcional `client_mutation_id`, opcional `queue_owner_technician_id`. |
| GET | `list_offline_sync_api/` | Query: `status`, `limit`, `offset`. Lista só itens do técnico autenticado. |
| POST | `process_offline_sync_api/<queue_id>/` | Aplica uma entrada `pending` ou reprocessa `conflict`. `success` é idempotente. |

## Contrato de `payload`

```json
{
  "schema_version": 1,
  "action": "checklist_batch_answers",
  "body": {
    "checklist_id": 123,
    "answers": [
      { "item_template": 10, "value": 150.0, "note": "" }
    ]
  }
}
```

Outra ação suportada:

- `checklist_submit` — `body`: `{ "checklist_id": 123 }` (equivale a `submit_checklist` no servidor).

Novas ações podem ser adicionadas em `core/services/offline_sync_service.py` (`process_offline_sync_item`).

## Fluxo recomendado no app

1. Sem rede: gravar localmente e, se possível, chamar `enqueue` com o mesmo payload quando a API estiver acessível **ou** guardar só local e enviar lote de `enqueue` ao reconectar.
2. Com rede: `process_offline_sync_api` para cada `queue_id` pendente (ou em série).
3. Usar sempre `client_mutation_id` (UUID) por mutação para evitar duplicar respostas ao repetir submit.

## Serviço

Implementação: `backend/apps/core/services/offline_sync_service.py`.
