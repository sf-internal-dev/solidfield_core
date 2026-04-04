# Guia — próximos passos para conectar Filehub e **sf-watermarker-worker-go**

Documento operacional para equipas **Django (solidfield_core)** e **Go / DevOps**. Complementa `FILEHUB_SF_WATERMARKER_ANALISE_INTEGRACAO.md` e `SF_WATERMARKER_INTEGRACAO_SOLIDFIELD.md` (raiz do repo).

---

## Pré-requisito de leitura

- Contrato HTTP do microsserviço: `POST /image_watermark_service_webhook`, header **`X-Tenant-ID`**, resposta **`202`** + `job_id` (+ `tenant_id`). Processamento **assíncrono** (NATS). O fecho do ciclo até ao Filehub segue a **decisão (A)** abaixo (object storage + webhook).

---

## Decisão registada — entrega do JPEG final (**opção A**)

**Escolha do produto / arquitetura (solidfield_core + sf-watermarker-worker-go):**

1. O **worker** envia o JPEG processado para **object storage** compatível com **S3 API** (AWS S3, MinIO, etc.).
2. O worker (ou um componente colado ao pipeline) chama um **webhook no Django** com, no mínimo: **`job_id`**, identificação do registo (`work_order_photo_id` ou equivalente acordado), e **localização do objeto** (**URL assinada** e/ou **bucket + key**).
3. O Django valida o pedido (autenticação mútua a definir na linha **0.2**), actualiza **`WorkOrderPhoto`** (e campos `watermark_status` / ficheiro final conforme modelo) de forma **idempotente**.

> **Nota:** até esta extensão existir no Go, o worker continua a gravar só em `OUTPUT_DIR`; a decisão (A) define o **alvo** de implementação, não o estado actual do binário.

---

## Fase 0 — Acordo cross-equipa (restante)

| # | Decisão | Estado | Notas |
|---|---------|--------|-------|
| 0.1 | **Entrega do JPEG final** | **✓ (A)** Object storage (S3/MinIO) + **webhook** Django (`job_id`, URL ou key) | Ver secção anterior. Opções (B) poll e (C) volume **não** são o caminho oficial. |
| 0.2 | **Segurança** Django ↔ Go (+ webhook de conclusão) | Aberto | API key, HMAC, mTLS, rede privada; proteger também o endpoint de callback. |
| 0.3 | **`X-Tenant-ID`** | Aberto | Ex.: `str(CompanyTenant.pk)` ou `tenant_code` — alinhar com payload do callback. |

---

## Fase 1 — Imagem original acessível ao worker (URL / storage)

O Go faz **GET** em `image_url` com **anti-SSRF** (IPs privados bloqueados por defeito).

| # | Tarefa | Detalhe |
|---|--------|--------|
| 1.1 | Definir **storage** em prod | Local `MEDIA_*` vs **S3** (`django-storages` ou equivalente). |
| 1.2 | Garantir URL que o **container Go consegue ler** | Preferir **URL assinada** (TTL curto) para o objeto; evitar depender de IP privado do Django sem política clara. Alternativa: **`image_base64`** no webhook (mais pesado). |
| 1.3 | Documentar uso de `ALLOW_PRIVATE_IPS` no Go | Só **desenvolvimento**; nunca como solução de prod. |

---

## Fase 2 — Modelo Django `WorkOrderPhoto`

| # | Tarefa | Campos sugeridos (ajustar a cada produto) |
|---|--------|---------------------------------------------|
| 2.1 | Migração | `watermark_job_id` (UUID/string, nullable até primeiro enqueue) |
| 2.2 | | `watermark_status`: ex. `none`, `pending`, `processing`, `completed`, `failed` |
| 2.3 | | `watermark_error` (texto curto, opcional) |
| 2.4 | Decisão de produto | **Uma** imagem (substituir `image` após watermark) vs **duas** (`image` original + `image_watermarked` ou URL no storage) |

Ficheiro actual: `backend/apps/filehub/models/os_photo.py`.

---

## Fase 3 — Cliente HTTP Django → sf-watermarker-worker-go

| # | Tarefa | Detalhe |
|---|--------|--------|
| 3.1 | Settings | `WATERMARKER_BASE_URL`, timeouts, política de retry |
| 3.2 | Montar `WebhookPayload` a partir do modelo | `work_reference` ← `WorkOrder.identifier`; `uploaded_by` ← técnico (nome ou id); `photo_taken_at`, GPS, `device_info`, `add_watermark`, `watermark_has_company_logo`; `company_logo_url` ← URL pública do `CompanyTenant.logo` se existir |
| 3.3 | Header `X-Tenant-ID` | Valor acordado na fase 0.3 |
| 3.4 | Mapear **`photo_type`** | Choices Django (`before`, `after`, `issue`, `proof`, `custom`) vs whitelist Go — alinhar ou tabela de mapeamento |
| 3.5 | Após `202` | Gravar `watermark_job_id` e `watermark_status=pending` (ou `processing`) |

Implementação recomendada: módulo dedicado, ex. `backend/apps/filehub/services/watermark_client.py` (nome à escolha da equipa).

---

## Fase 4 — Quando disparar o watermarker

| # | Tarefa | Detalhe |
|---|--------|--------|
| 4.1 | **`transaction.on_commit`** | Chamar o cliente HTTP **depois** do commit que persiste `WorkOrderPhoto` e o ficheiro — evita jobs se a transação falhar |
| 4.2 | Flag `add_watermark` | Se `False`, não enviar ao Go (ou só pipeline de “normalização JPEG”, se acordado com o time Go) |
| 4.3 | Falhas de rede | Retry idempotente: definir se o mesmo `job_id` pode ser reutilizado ou se se cria nova linha/registo |

---

## Fase 5 — Endpoint de conclusão no Django (quando fase 0.1 = callback)

| # | Tarefa | Detalhe |
|---|--------|--------|
| 5.1 | Rota interna | Ex. `POST /internal/watermark-complete/` (não expor à internet sem protecção) |
| 5.2 | Corpo | `job_id`, estado, URL final do JPEG ou conteúdo referenciado por key em S3 |
| 5.3 | Actualizar `WorkOrderPhoto` | Preencher campo(s) de imagem final + `watermark_status=completed` ou `failed` |
| 5.4 | **Idempotência** | O mesmo `job_id` pode ser notificado mais de uma vez |

---

## Fase 6 — API pública Filehub (app de campo)

| # | Tarefa | Detalhe |
|---|--------|--------|
| 6.1 | `POST` (multipart) | Criar `WorkOrderPhoto` para uma `work_order_id`; validar tenant e técnico |
| 6.2 | `GET` | Listar / detalhar fotos da OS |
| 6.3 | OpenAPI | `@extend_schema` com `operation_id` estáveis (Public v1), alinhado a `API_PUBLIC_CONTRACT.md` |
| 6.4 | Registo | Incluir rotas em `backend/apps/apis/urls.py` |

---

## Fase 7 — Limpezas recomendadas (paralelas)

| # | Tarefa | Onde |
|---|--------|------|
| 7.1 | Corrigir uso de `work_order.from_user` | `backend/apps/core/services/audition_log_service.py` — `WorkOrder` tem `created_by`, não `from_user` |
| 7.2 | Corrigir testes | `backend/apps/filehub/tests/test_photo.py` — usar `work_order`, `photo_taken_at`; `test_signature.py` — import `WorkOrderSignature` |

---

## Fase 8 — Depois do MVP (não bloqueia o primeiro fio)

| # | Tarefa | Detalhe |
|---|--------|--------|
| 8.1 | FK opcional checklist / item | `WorkOrderPhoto` → `Checklist` / `ChecklistItemTemplate` (pesca MVP) |
| 8.2 | `OfflineSyncQueue` | Nova acção para upload de foto offline — quotas, tamanho máximo, retry |

---

## Ordem sugerida num sprint

1. **Fase 0** — `0.1` **fechado** (S3/MinIO + webhook); fechar **`0.2`** segurança e **`0.3`** `X-Tenant-ID` + formato do callback.  
2. **Fase 1** + **Fase 2** em paralelo (DevOps + Django).  
3. **Fase 3** + **Fase 4** (disparo assíncrono funcionando com `202`).  
4. **Fase 5** assim que o Go (ou orquestrador) entregue o fecho (callback/storage).  
5. **Fase 6** para o app.  
6. **Fase 7** quando possível.  
7. **Fase 8** conforme roadmap pesca.

---

## Documentos relacionados

| Ficheiro | Conteúdo |
|----------|----------|
| `FILEHUB_SF_WATERMARKER_ANALISE_INTEGRACAO.md` | Análise estado actual vs gaps |
| `BRIEFING_PARA_FILEHUB_PESCA_MVP.md` | Produto pesca + extensão checklist |
| `SF_WATERMARKER_INTEGRACAO_SOLIDFIELD.md` | Contrato técnico do microsserviço Go |
| `DOCUMENTACAO_PESCA_INDUSTRIAL_LARGA_ESCALA.md` | Vista macro do vertical |

---

*Guia de trabalho — actualizar quando o callback/storage e as rotas internas estiverem definidos no código.*
