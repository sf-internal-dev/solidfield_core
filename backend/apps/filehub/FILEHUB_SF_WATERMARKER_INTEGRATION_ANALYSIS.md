# Análise — Filehub + **sf-watermarker-worker-go** no solidfield_core

Este documento cruza o estado **real** do app `filehub` neste repositório com a especificação **`SF_WATERMARKER_INTEGRACAO_SOLIDFIELD.md`**, para orientar o trabalho de integração (APIs Django, modelo, segurança, fecho do ciclo assíncrono).

---

## 1. Estado actual do Filehub (código)

| Aspecto | Situação |
|---------|----------|
| **Modelos** | `WorkOrderPhoto`, `WorkOrderSignature` — ambos ligados a `orders.WorkOrder` + `Technician`. |
| **APIs REST** | **Não existem** entradas em `backend/apps/apis/urls.py` para upload/listagem de fotos ou assinaturas. |
| **Uso operacional** | Sobretudo **Django Admin** (inlines na `WorkOrder`). |
| **Alinhamento com watermarker** | `WorkOrderPhoto` já tem `add_watermark`, `watermark_has_company_logo`, metadados (GPS, `device_info`, `photo_taken_at`, `photo_type`) — **espelham o contracto semântico** do webhook Go. |
| **Checklist / pesca** | **Sem FK** para `Checklist` ou `ChecklistItemTemplate`; vínculo ao diário é hoje só via **mesma `WorkOrder`** + texto em `description` / convenção (ver `BRIEFING_PARA_FILEHUB_PESCA_MVP.md`). |
| **Testes** | `test_photo.py` usa `service_order` e omite `photo_taken_at` — **desalinhado** com o modelo actual (`work_order`, `photo_taken_at` obrigatório). `test_signature.py` importa `ServiceOrderSignature` (nome inexistente). **Test suite do filehub não reflete o código.** |
| **Auditoria** | `log_work_order_photo_upload` / `log_work_order_client_signature_upload` usam `work_order.from_user`; em `WorkOrder` o campo é **`created_by`**, não `from_user` — **bug / débito técnico** ao integrar upload real. |
| **Media / storage** | `ImageField` com `upload_to` local; `settings.py` **não define** `MEDIA_URL` / `MEDIA_ROOT` explicitamente (comum em dev; em produção costuma ser S3 ou path servido). Implica **estratégia clara de URL** para o Go fazer `GET` da imagem original. |

---

## 2. Estado do **sf-watermarker-worker-go** (resumo do contrato)

| Aspecto | Implicação para o core |
|---------|-------------------------|
| Entrada | `POST /image_watermark_service_webhook`, JSON; **`X-Tenant-ID` obrigatório**. |
| Imagem | `image_url` **ou** `image_base64`. |
| Resposta | **`202`** + `{ job_id, tenant_id }` — processamento **assíncrono** (NATS JetStream). |
| Saída | Ficheiro **`{OUTPUT_DIR}/{job_id}.jpg`** no disco do worker — **não atualiza** Django nem Filehub. |
| Segurança URL | Anti-**SSRF**: IPs privados bloqueados por defeito (`ALLOW_PRIVATE_IPS=true` só dev). |
| `photo_type` | Whitelist Go pode **não coincidir** com `PHOTO_TYPE_CHOICES` do Django (`before`, `after`, `issue`, `proof`, `custom`) — precisa **mapeamento** ou extensão num dos lados. |
| Logo empresa | `company_logo_url` (HTTP(S)); no core existe `CompanyTenant.logo` — candidato natural a originar URL **pública** (ou proxy assinado). |

---

## 3. Lacuna central: fechar o ciclo **original → job → imagem final no Filehub**

O doc do watermarker descreve correctamente o gap:

1. Hoje o Go **não** faz callback nem grava no storage do produto.
2. O core **não** persiste `job_id` nem estado (`pending` / `done` / `failed`).
3. É necessário **um** dos padrões abaixo (ordem = recomendação pragmática).

### Opção A — Object storage + notificação (melhor para produção) — **DECISÃO ADOPTADA**

Esta é a via escolhida para o **solidfield_core**: fechar o ciclo com **S3-compatible storage + webhook de conclusão** para Django (ver `GUIA_PROXIMOS_PASSOS_FILEHUB_WATERMARKER.md`).

1. Após o worker gerar o JPEG, **enviar para S3** (ou bucket único path por tenant).
2. **Webhook de conclusão** para Django com `job_id`, URL final e/ou **bucket + key**, e identificador do registo (`work_order_photo_id` ou equivalente).
3. Django actualiza `WorkOrderPhoto` (campo `image` ou campo separado `image_watermarked`) e `watermark_status=done` (idempotente).

### Opção B — Poll `GET /jobs/{id}` + download (extensão do serviço Go)

- Exige implementação **no watermarker**; o doc indica que **ainda não existe**.

### Opção C — Volume partilhado / agente

- Django ou agente copia `{job_id}.jpg` para `MEDIA_ROOT` e actualiza o registo.
- Frágil em Kubernetes/multi-instância; útil só em dev ou single node.

**Conclusão:** sem **A ou B**, o Filehub não fica “integrado de ponta a ponta” — apenas **dispara** o job.

---

## 4. Problema crítico: **`image_url` legível pelo worker**

O worker faz `GET` na URL com timeout 15s. Para usar **foto já gravada** no Django:

- A URL tem de ser **acessível a partir da rede onde o container Go corre** (não basta path local).
- Se a URL apontar para o **Django atrás de IP privado** (ex.: `http://10.x/.../media/...`), o Go **rejeita** por SSRF — correcto em prod.
- **Mitigações típicas:**
  - **URL assinada** (S3/MinIO) pública temporariamente na mesma rede que o worker pode alcançar sem ser “private IP” interno mal definido; ou
  - **Mesmo VPC** com excepção controlada (documentar risco); ou
  - **base64** no webhook (pesado para fotos grandes, mas evita fetch).

Isto deve ser decidido em conjunto com **DevOps** e a documentação do watermarker (`ALLOW_PRIVATE_IPS` só para dev).

---

## 5. Modelo `WorkOrderPhoto` — campos a considerar na integração

| Campo existente | Uso com watermarker |
|-----------------|---------------------|
| `image` | Guardar **original** até haver política clara; ou substituir pela **versão final** após watermark (perde-se original a menos que duplique campo). |
| `add_watermark` / `watermark_has_company_logo` | Controlam se se chama o webhook e `company_logo_url`. |
| *(proposto)* `watermark_job_id` | UUID retornado no `202`. |
| *(proposto)* `watermark_status` | ex.: `pending`, `processing`, `completed`, `failed` — ou reutilizar flags simples. |
| *(proposto)* `image_original` | Se o produto quiser **manter** original + watermarked (2 ficheiros). |

**Decisão de produto:** uma imagem só (substituir) vs. duas (compliance / contestação).

---

## 6. `X-Tenant-ID` — o que enviar

O header é obrigatório no Go. Acordar valor estável:

- **`str(CompanyTenant.pk)`** (simples); ou  
- **`tenant_code`** / **slug** (se único e imutável o suficiente).

O mesmo valor deve aparecer em logs e em futuras correlações webhook de conclusão.

**Nota:** isto **não substitui** RBAC no Django; é rótulo para o worker e JetStream.

---

## 7. Fluxo recomendado (alto nível) para implementação no core

1. **API** `POST` upload (multipart) → cria `WorkOrderPhoto` com ficheiro original, valida `work_order.tenant` vs técnico.
2. Se `add_watermark`:
   - Construir payload do webhook (mapeamento de campos na secção 8 do `SF_WATERMARKER_INTEGRACAO_SOLIDFIELD.md`).
   - Obter `image_url` ** válida para o worker** OU enviar `image_base64`.
   - `POST` ao Go com `X-Tenant-ID`.
   - Persistir `job_id` + `watermark_status=pending`.
3. **Assíncrono:** worker processa → **(falta implementar)** entrega final → Django actualiza foto + `watermark_status=completed`.
4. Se `add_watermark=False`, opcionalmente ainda pode chamar o Go “só normalização JPEG” conforme flag do serviço — ver doc Go.

**Disparador técnico:** signal `post_save`, Celery, `transaction.on_commit` + HTTP assíncrono, ou comando dedicado — evitar bloquear request se o Go estiver lento (embora o `202` seja rápido, a rede pode falhar).

---

## 8. Offline (`OfflineSyncQueue`) e fotos

- Respostas de checklist já têm acções na fila; **fotos** podem ser:
  - upload **directo** quando há rede (multipart para nova API), ou  
  - nova acção `filehub_photo_upload` com payload (metadados + base64 chunking ou referência a blob local) — **mais trabalho** e limites de tamanho.
- Recomendação MVP: **upload online primeiro**; offline de fotos como **fase 2** com desenho de quota e retry.

---

## 9. OpenAPI “Public v1”

- Endpoints Filehub deverão receber `@extend_schema` com `operation_id` estáveis quando existirem, alinhado ao resto do contrato (`API_PUBLIC_CONTRACT.md`).

---

## 10. Documentação cruzada

| Ficheiro | Papel |
|----------|--------|
| `SF_WATERMARKER_INTEGRACAO_SOLIDFIELD.md` | Contrato do microsserviço Go; gaps e padrões A/B/C. |
| `BRIEFING_PARA_FILEHUB_PESCA_MVP.md` | Pedido de produto pesca + extensão checklist. |
| `DOCUMENTACAO_PESCA_INDUSTRIAL_LARGA_ESCALA.md` | Vista macro do vertical. |

**Nota:** `SF_WATERMARKER_INTEGRACAO_SOLIDFIELD.md` referencia `HANDOFF_BACKEND_FILEHUB_PESCA_INDUSTRIAL.md` — **ficheiro inexistente** neste repo; usar `BRIEFING_PARA_FILEHUB_PESCA_MVP.md` ou este documento como referência Django.

---

## 11. Checklist de trabalho (engenharia)

- [ ] Corrigir testes `filehub` e `audition_log_service` (`from_user` → `created_by` ou `uploaded_by`).
- [ ] Definir `MEDIA_*` / storage alinhado com URL para o worker.
- [ ] Implementar APIs Filehub + permissões.
- [ ] Client HTTP ao watermarker (timeouts, retries idempotentes com mesmo `job_id` se aplicável).
- [ ] Migração: `watermark_job_id`, `watermark_status` (+ opcional segundo ficheiro).
- [ ] Fecho do ciclo: **callback Go** ou **S3 + evento** (acordar com repo do watermarker).
- [ ] Mapeamento `photo_type` Django ↔ validação Go.
- [ ] (Opcional) FK opcional `WorkOrderPhoto` → checklist / item template para p MVP pesca.
- [ ] Documentar `X-Tenant-ID` e segurança (API key / mTLS entre Django e Go em produção — hoje o webhook só valida tenant header).

---

*Análise consolidada para alinhar desenvolvimento Filehub com **sf-watermarker-worker-go**.*
