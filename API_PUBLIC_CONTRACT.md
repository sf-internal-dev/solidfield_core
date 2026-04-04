# Public API v1 — contrato e estabilidade

Este documento descreve a política do pacote **Public v1 — Field operations** documentado no OpenAPI (`SPECTACULAR_SETTINGS.VERSION` = `1.0.0`).

## Onde ver o schema

- **Swagger UI:** `GET /api/docs/` (servidor Django em execução).
- **OpenAPI JSON/YAML:** `GET /api/schema/` (formato negociável pelo header `Accept`).

## Exportar o schema localmente

Na raiz do repositório (`solidfield_core/`), com o ambiente Python do projeto ativo:

```bash
python manage.py spectacular --file openapi.yaml
python manage.py spectacular --validate
```

## Versionamento

- Alterações **compatíveis** (campos opcionais novos, códigos de erro adicionais documentados) podem ocorrer em `1.0.x`.
- Alterações **incompatíveis** (remoção de campos, mudança de semântica de códigos HTTP, renomeação de `operation_id`) exigem incremento de versão major (ex.: `2.0.0`) e migração para clientes.

## Autenticação

Os endpoints públicos v1 seguem a mesma política de autenticação do restante da API DRF do projeto (ex.: JWT / sessão, conforme `REST_FRAMEWORK` em `backend/config/settings.py`). Consulte o schema gerado para security schemes efetivos.

## Endpoints estáveis (tags Public v1)

Rotas são montadas sob o prefixo **`/api/`** conforme `backend/apps/apis/urls.py`. Lista resumida:

| Área | Exemplos de rotas |
|------|-------------------|
| Work orders | `create_work_order_api/`, `list_work_orders_api/`, `get_work_order_api/<id>/`, `update_work_order_api/<id>/`, `assign_work_order_api/<id>/`, `get_work_order_status_history_api/<id>/` |
| Checklist | rotas em `checklist_api` (criar, respostas em lote, listagem, submit, progresso, export CSV, etc.) |
| Offline sync | rotas em `offline_sync_api` (enqueue, list, process) |

Os nomes de operação estáveis para geradores de cliente são os **`operation_id`** no OpenAPI (prefixo `publicV1…`).

## Erros comuns documentados

- **422:** corpo com `codes` (lista de strings de domínio) e opcionalmente `correlation_id` (publicação de mensagens UI).
- **400:** validação simples em alguns POST (ex.: campo obrigatório ausente).

Para detalhes exatos por rota, use o arquivo OpenAPI exportado ou `/api/docs/`.
