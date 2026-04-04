# Briefing para o sistema Filehub — integração com MVP Pesca industrial

**Destinatário:** equipa / responsáveis pelo **Filehub** no ecossistema SolidField.  
**Objetivo deste documento:** pedir que o Filehub devolva um **`.md` técnico detalhado** com o funcionamento real do módulo (APIs, modelo de dados, regras, limites), para amarrarmos **evidências fotográficas (e, se aplicável, assinaturas)** ao fluxo **Diário operacional — Pesca industrial** sem reinventar contratos.

**Resposta esperada:** ficheiro Markdown (ex.: `FILEHUB_ESPECIFICACAO_TECNICA.md`) cobrindo os tópicos da secção 6.

---

## 1. Contexto do produto (lado checklist / pesca)

- O vertical **pesca industrial (larga escala)** usa o app `checklist` com template semeado **`pesca_industrial_diario`** (`service_type`: `pesca_industrial_diario`), itens como consumo de diesel (L), gelo (kg), temperatura da câmara (°C), turno, observações.
- Cada **execução** de checklist pode estar vinculada a uma **`WorkOrder`** (viagem / OS) via campo opcional na criação do checklist.
- O **servidor** já expõe APIs de checklist, export CSV, work orders e **fila offline** (`OfflineSyncQueue`) para lote de respostas e submit — ver `DOCUMENTACAO_PESCA_INDUSTRIAL_LARGA_ESCALA.md` na raiz do repositório.
- **Necessidade de produto:** anexar **fotos com contexto de campo** (ex.: painel de horímetro/combustível, leitura de termômetro, estado do gelo) para reduzir contestação e suportar auditoria. Idealmente a evidência fica **encontrável** pela combinação **viagem (`work_order_id`) + checklist + item do template** (ou um código de “tipo de evidência” acordado).

---

## 2. O que o Filehub é **hoje** neste repositório (estado real)

No código atual do `solidfield_core`, o app `backend.apps.filehub` contém sobretudo **modelos Django** e **admin**, não rotas REST listadas em `backend/apps/apis/urls.py`.

### 2.1 `WorkOrderPhoto`

- **Ligação:** `ForeignKey` para `orders.WorkOrder` (`related_name="photos"` no modelo).
- **Quem enviou:** `ForeignKey` para `core.Technician` (`uploaded_by`).
- **Ficheiro:** `ImageField` (`upload_to="service_photos/"`).
- **Tempo:** `photo_taken_at` (obrigatório no modelo), `uploaded_at` (auto na criação).
- **Tipo semântico:** `photo_type` — valores: `before`, `after`, `issue`, `proof`, `custom`.
- **Opcionais:** `description`, `gps_latitude`, `gps_longitude`, `device_info`, `add_watermark`, `watermark_has_company_logo`.

Ficheiro: `backend/apps/filehub/models/os_photo.py`.

### 2.2 `WorkOrderSignature`

- **Ligação:** `ForeignKey` para `orders.WorkOrder` (`related_name="signature"` no modelo).
- **Ordem / cliente:** `ordered_by` (técnico), `signed_by` (texto), `image`, `signed_at`, opcionais `latitude`, `longitude`, `ip_address`.

Ficheiro: `backend/apps/filehub/models/os_signature.py`.

### 2.3 Integrações já tocadas

- **Admin:** inlines de foto e assinatura na OS (`orders` admin).
- **Auditoria:** funções em `backend/apps/core/services/audition_log_service.py` que referem upload de foto/assinatura (convém alinhar `action_code` e uso de `work_order.from_user` com o modelo real da `WorkOrder` quando documentarem).

### 2.4 Lacuna explícita

- **Não há** endpoints públicos documentados no OpenAPI “Public v1” para upload/listagem de ficheiros do Filehub neste passo.
- **Não há** `ForeignKey` dos modelos Filehub para `checklist.Checklist` ou `ChecklistItemTemplate` — hoje o vínculo natural é só **`WorkOrder` + metadados** (`photo_type`, `description`).

---

## 3. O que o fluxo “Pesca MVP” precisa do Filehub

| Necessidade | Detalhe |
|-------------|---------|
| Upload a partir do app de campo | Multipart ou URL pré-assinada; autenticação alinhada ao técnico / tenant. |
| Amarração mínima | `work_order_id` obrigatório; **opcional desejável:** `checklist_id`, `checklist_item_template_id` ou string `evidence_code` para cruzar com o diário. |
| Metadados | GPS opcional, timestamp de captura, tipo de foto (reutilizar `photo_type` ou enum estendido para pesca). |
| Listagem / download | Para o técnico ou backoffice ver evidências da viagem (e, no futuro, export conjunto com CSV do checklist). |
| Multi-tenant | Garantir isolamento coerente com `WorkOrder.tenant` / técnico. |
| Offline | O cliente pode guardar fotos localmente; ao sincronizar, precisamos de **estratégia** (upload direto vs fila tipo `OfflineSyncQueue` com payload de upload — a definir convosco). |

Assinatura de **cliente final** pode ser **fora do MVP pesca** (foco em foto de evidência operacional).

---

## 4. Proposta de extensão de modelo (para discussão)

Se quiserem amarrar “foto do item 6 do diário” sem ambiguidade, uma das opções:

- **A)** Campos opcionais em `WorkOrderPhoto`: `checklist`, `checklist_item_template` (ou apenas IDs inteiros nullable).
- **B)** Manter só `WorkOrder` + `description` / `photo_type` padronizado (`custom` + texto tipo `checklist:123:item:45`).
- **C)** Tabela de ligação N:N ou modelo “AttachmentMetadata” separado.

Precisamos da vossa recomendação (**performance, migrações, padrão atual do Filehub**).

---

## 5. O que este projeto entregará de volta depois da vossa documentação

- Rotas DRF (ou consumo do vosso serviço) alinhadas ao contrato que descreverem.
- Possible extension of `OfflineSyncQueue` actions para **registar upload pendente**, se o fluxo for assíncrono.
- Atualização do OpenAPI Public v1 para operações de evidência, se fizer parte do pacote MVP fechado.

---

## 6. Checklist do que pedimos no `.md` de retorno (minucioso)

Por favor incluir:

1. **Inventário:** modelos, relações, `upload_to`, storage (local/S3/etc.), tamanho máximo, formatos aceites.
2. **APIs existentes ou planeadas:** método, path, auth, corpo, respostas, códigos de erro, paginação.
3. **Permissões:** que ação RBAC / nível técnico pode criar, listar, apagar anexos.
4. **Watermark / pós-processamento:** se é síncrono, fila, ou só flag no modelo.
5. **URLs públicas vs internas:** como o app obtém thumbnails ou download seguro.
6. **Auditoria:** eventos disparados ao upload; consistência com `audition_log_service`.
7. **Multi-tenant:** validações ao associar `work_order_id` ao técnico autenticado.
8. **Assinaturas:** quando usar `WorkOrderSignature` vs foto; requisitos legais que conheçam.
9. **Limitações conhecidas** e roadmap curto do Filehub.
10. **Exemplo completo:** fluxo “criar OS → tirar foto → associar → listar” com `curl` ou equivalente.

---

## 7. Contacto lógico entre equipas

- **Consumidor principal:** app `checklist` + APIs em `backend/apps/apis/urls.py` + fila `core` (offline).
- **Documentação de domínio checklist:** `backend/apps/checklist/CHECKLIST_SCHEMA.md`.
- **Itens do seed pesca:** `backend/apps/checklist/defaults/pesca_diario_operacional.py` (nomes e ordem dos itens para alinhar códigos de evidência).

---

*Documento gerado para handoff Filehub ↔ vertical Pesca MVP. Ajustar datas e donos de decisão conforme o vosso processo interno.*
