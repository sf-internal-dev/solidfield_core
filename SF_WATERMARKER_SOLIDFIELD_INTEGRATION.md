# sf-watermarker-worker-go — especificação técnica e integração com SolidField (Filehub / solidfield_core)

**Audiência:** equipas backend (Django), Filehub, DevOps, produto.  
**Âmbito deste repositório:** o código **deste** projeto; a ligação ao **solidfield_core** é descrita em termos de **contrato e arquitetura alvo**, salvo onde se indica explicitamente o contrário.

---

## 1. O que é o sf-watermarker-worker-go

É um **microsserviço autónomo** em **Go** cuja única responsabilidade é:

1. Receber um pedido para **processar uma imagem** (vinda por **URL HTTP(S)** ou **base64**).
2. Opcionalmente aplicar **marca d’água** (painel de metadados + logos).
3. **Enfileirar** o trabalho e responder de imediato com um identificador de job (**assíncrono**).
4. Um **worker** consome a fila, processa e **grava o resultado** como **JPEG** num diretório configurável (`OUTPUT_DIR`).

Não gere utilizadores, permissões de OS, storage definitivo de produto nem checklist — isso pertence ao **solidfield_core** (Django) e ao módulo **Filehub**. Este serviço é um **motor de imagem + fila** pensado para ser chamado **a partir** do ecossistema SolidField (ou outro orquestrador) quando `add_watermark` (ou regra equivalente) estiver activa.

---

## 2. Objectivos de produto e técnicos

| Objectivo | Descrição |
|-----------|-----------|
| **Desacoplar** o processamento pesado de imagem da API Django | Evitar timeouts e bloquear menos workers WSGI/ASGI durante decode, resize e composição. |
| **Escalar horizontalmente** | Vários processos do mesmo binário com **consumers NATS** diferentes (`NATS_CONSUMER`). |
| **Metadados de campo na imagem** | Texto legível (técnico, data, GPS, contexto, obra, dispositivo) para **auditoria** e menor contestação (alinhado a verticais como pesca industrial / checklist). |
| **Marcas visuais** | Logo do **software** (embutida no binário) e, opcionalmente, logo da **empresa** (URL HTTP). |
| **Formatos reais de telemóvel** | Pipeline de decode com **EXIF/orientação**; **HEIF/HEIC/AVIF** com build `heif` + CGO (ver README). |

---

## 3. Stack e componentes

| Componente | Tecnologia | Papel |
|------------|------------|--------|
| API HTTP | **Gin** | Webhook JSON, health checks. |
| Fila | **NATS JetStream** | Stream tipo work queue, subject configurável, `MsgId` = `job_id` (deduplicação no publish). |
| Processamento de imagem | `disintegration/imaging`, `golang.org/x/image`, **goexif**, opcionalmente **goheif** | Resize, overlay, texto, orientação JPEG, HEIF. |
| Persistência **neste serviço** | Sistema de ficheiros local | `{OUTPUT_DIR}/{job_id}.jpg` — **não** é o `ImageField` do Django. |
| Tenancy na API | Header **`X-Tenant-ID`** | Obrigatório para o webhook; é **ecoado** na resposta 202 e guardado na mensagem da fila; **não** substitui RBAC no core. |

---

## 4. Arquitectura de execução (processo único)

No arranque (`cmd/main.go`):

1. Garante `OUTPUT_DIR`.
2. Carrega a **logo do software** (PNG embutido em `assets/`).
3. Liga ao **NATS**, cria stream JetStream se não existir (retenção ~24h nas mensagens).
4. Instancia **`FileStorage`** + **`Worker`** (com `MAX_DIM`).
5. Subscreve o consumer e arranca **goroutine** de pull/fetch de mensagens (ack explícito: sucesso → `Ack`, falha → `Nak` / retry).
6. Arranca o **servidor HTTP** Gin noutra goroutine.
7. **Graceful shutdown** do processo: SIGINT/SIGTERM (o HTTP pode terminar abruptamente conforme implementação actual).

Fluxo de um job:

```
Cliente HTTP ──POST /image_watermark_service_webhook──► Gin
       │ valida JSON + tenant
       ▼
  gera job_id (UUID)
       ▼
  publica JobMessage no JetStream (MsgId = job_id)
       ▼
  responde 202 { job_id, tenant_id }

Worker (loop) ──fetch──► deserializa JobMessage
       ▼
  carrega imagem (URL ou base64)
       ▼
  resize se > MAX_DIM
       ▼
  se add_watermark: compose + logos; senão: só grava
       ▼
  SaveImage(job_id) → OUTPUT_DIR/{job_id}.jpg
       ▼
  Ack da mensagem NATS
```

---

## 5. API HTTP (contrato actual)

### 5.1 Endpoints

| Método | Path | Resposta |
|--------|------|----------|
| `GET` | `/healthz` | `200` texto `ok` |
| `GET` | `/readyz` | `200` texto `ready` |
| `POST` | `/image_watermark_service_webhook` | Ver abaixo |

### 5.2 Webhook — autenticação e erros

- **Tenant:** header **`X-Tenant-ID`** obrigatório e não vazio. Se faltar → **`401`** `{ "error": "unauthorized" }`.
- **Corpo:** JSON; falha de parse → **`400`** `bad_request`.
- **Validação de negócio** → **`400`** `invalid_payload` com mapa `fields` ou `details`.
- **Fila indisponível** (falha ao publicar) → **`503`** `queue_unavailable`.

### 5.3 Corpo JSON (`WebhookPayload`)

Campos (espelhados em `internal/httpapi/types.go` e `internal/queue/types.go` — devem manter-se alinhados):

| Campo JSON | Tipo | Notas |
|------------|------|--------|
| `image_url` | string | Pelo menos um de `image_url` ou `image_base64`. |
| `image_base64` | string | Base64 standard da imagem. |
| `photo_type` | string | Ex.: `installation`, `maintenance` (validação parcial / whitelist em `validators.go`). |
| `uploaded_by` | string | **Obrigatório** (auditoria / overlay). |
| `photo_taken_at` | string | ISO 8601 se preenchido. |
| `work_reference` | string | Ex.: código da OS — útil para overlay “Work: …”. |
| `location_label` | string | Texto legível de local. |
| `photo_context` | string | Ex.: antes/depois de instalação. |
| `add_watermark` | bool | Se `false`, só normaliza e grava JPEG sem painel. |
| `watermark_has_company_logo` | bool | Se `true` e watermark activo → exige `company_logo_url`. |
| `watermark_has_software_logo` | bool | Inclui logo SolidField embutida. |
| `gps_latitude` / `gps_longitude` | float64 opcional | Ambos ou nenhum. |
| `device_info` | string | Overlay. |
| `company_logo_url` | string | HTTP(S); validação anti-SSRF (bloqueio de IP privado salvo `ALLOW_PRIVATE_IPS=true`). |

### 5.4 Resposta de sucesso (enqueue)

**`202 Accepted`**

```json
{
  "job_id": "<uuid>",
  "tenant_id": "<valor do header X-Tenant-ID>"
}
```

### 5.5 Segurança em URLs

- Apenas esquemas `http` / `https`.
- **Anti-SSRF:** IPs em redes privadas, loopback, link-local, ULA IPv6 são **rejeitados** por defeito; em desenvolvimento pode usar-se `ALLOW_PRIVATE_IPS=true`.

---

## 6. Fila NATS JetStream

| Variável | Padrão |
|----------|--------|
| `NATS_URL` | `nats://localhost:4222` |
| `NATS_STREAM` | `WATERMARK_JOBS` |
| `NATS_SUBJECT` | `watermark.jobs` |
| `NATS_CONSUMER` | `watermark-worker-1` |

**Mensagem (`JobMessage`):** `{ "job_id", "tenant_id", "payload": { ... mesmo JSON do webhook ... } }`.

**Comportamento:** work queue, `MaxAckPending` 100, fetch de 1 mensagem com espera até 5s, retry em falha de processamento.

**Limitação operacional:** o resultado fica só em **disco local** deste serviço; **não** há notificação HTTP de volta ao Django nesta versão do código.

---

## 7. Pipeline de imagem (resumo)

1. **Fonte:** `internal/source` — GET com timeout 15s e headers `User-Agent` / `Referer`, ou decode base64.
2. **Decode:** `internal/imaging.DecodeImageWithEXIF` — PNG, JPEG+EXIF orientation, sniff HEIF/AVIF (com tag `heif`), fallback genérico (ex. WebP).
3. **Resize:** `imaging.Fit` até `MAX_DIM` (default 1600).
4. **Composição:** `internal/compose.ComposeWatermark` — moldura, painel inferior direito com texto (wrap), barra de destaque, sombras; logos acima do painel.
5. **Gravação:** `internal/storage` — JPEG qualidade 92, nome `{job_id}.jpg`.

**Fontes embutidas:** `assets/` (WorkSans + logo) via `go:embed`.

---

## 8. Onde entra o solidfield_core e o Filehub

O **solidfield_core** é o **monólito Django** (APIs, tenants, técnicos, **WorkOrder**, **checklist**, etc.). O **Filehub** é a app Django que modela anexos ligados à OS, nomeadamente **`WorkOrderPhoto`** (`backend/apps/filehub/models/os_photo.py`).

### 8.1 Alinhamento semântico (já previsto nos modelos)

O modelo `WorkOrderPhoto` inclui campos que **mapeiam naturalmente** para o webhook deste serviço:

| Conceito Filehub (Django) | Campo / uso | Webhook Go |
|---------------------------|-------------|------------|
| Ficheiro da foto | `ImageField` — após upload, URL **pública ou assinada** legível pelo worker | `image_url` |
| Alternativa | Corpo binário em base64 (menos comum para fotos grandes) | `image_base64` |
| Quem enviou | `uploaded_by` (FK Technician → usar nome ou id na string) | `uploaded_by` |
| Momento da captura | `photo_taken_at` | `photo_taken_at` |
| Tipo semântico | `photo_type` (`before`, `after`, `issue`, `proof`, `custom`) | `photo_type` (pode exigir **mapeamento** ou extensão de enum de um lado) |
| GPS | `gps_latitude`, `gps_longitude` | `gps_latitude`, `gps_longitude` |
| Dispositivo | `device_info` | `device_info` |
| Watermark | `add_watermark`, `watermark_has_company_logo` | `add_watermark`, `watermark_has_company_logo` |
| Logo empresa | URL configurável por tenant / campo futuro | `company_logo_url` |
| Referência à obra | código da `WorkOrder` ou referência externa | `work_reference` |
| Contexto checklist / pesca | `description` ou FKs futuras (`checklist`, item) | `photo_context`, `location_label` |

O **tenant** Django deve propagar-se como **`X-Tenant-ID`** no pedido ao microsserviço (valor estável acordado entre sistemas — ex. slug ou UUID do tenant).

### 8.2 O que **não** está implementado neste repositório

- Chamadas HTTP **de** `solidfield_core` **para** este serviço.
- Modelo Django com campo `watermark_job_id` ou estados `pending/processing/done`.
- **Callback** do worker Go para actualizar `WorkOrderPhoto` ou enviar o ficheiro final para o **mesmo** `ImageField` / S3.
- Autenticação mútua (HMAC, mTLS, API key) entre Django e Go — o webhook actual só exige `X-Tenant-ID`.

Isto é **integração a construir** no core (e opcionalmente endurecimento no Go).

### 8.2.1 Decisão de arquitetura no **solidfield_core** (registada)

O ecossistema **SolidField / Filehub** adoptou o **padrão A** para a entrega do JPEG final:

- O **sf-watermarker-worker-go** (após implementação) **grava o resultado em object storage** (API compatível com S3, ex. MinIO) e invoca um **webhook no Django** com `job_id`, referência ao `WorkOrderPhoto` (ou id interno acordado) e **URL assinada** e/ou **bucket + key**.
- Detalhe operacional: `backend/apps/filehub/GUIA_PROXIMOS_PASSOS_FILEHUB_WATERMARKER.md`.

Isto substitui para fins de planeamento as opções B (poll) e C (volume partilhado em produção).

### 8.3 Padrões de integração recomendados (para o core)

**A — Pós-upload assíncrono (alinhado ao 202 + job_id)** — **padrão oficial SolidField**  
1. Cliente ou Django grava `WorkOrderPhoto` (ficheiro original ou URL temporária).  
2. Se `add_watermark`, serviço Django (signal, Celery, ou serviço dedicado) faz **POST** ao webhook com `image_url` apontando para uma URL que o worker consiga ler (**assinada**, TTL curto, ou rede interna com regra SSRF no worker).  
3. Django persiste `job_id` e estado “watermark pendente”.  
4. **Gap actual:** o Go só escreve em `OUTPUT_DIR`. **Decisão SolidField (§8.2.1):** implementar **upload para object storage (S3/MinIO)** + **webhook de conclusão** para Django; poll e volume partilhado ficam fora do caminho oficial.

**B — Síncrono no core (não é o desenho actual do Go)**  
O serviço Go foi desenhado para **202 + fila**; para fluxo síncrono seria preciso outro endpoint ou alteração de produto.

**C — Publicação directa na fila NATS a partir do Django**  
Possível em teoria (mensagem igual a `JobMessage`), mas duplica lógica de validação e expõe NATS ao core; normalmente **HTTP ao microsserviço** mantém fronteira mais clara.

### 8.4 Checklist / Pesca industrial

O briefing de produto pede amarração **WorkOrder + checklist + item**. O **Filehub** ainda não tem FK para checklist; até lá, `work_reference` + `photo_context` / `description` podem transportar referências legíveis. Quando existirem FKs ou `evidence_code`, o **solidfield_core** pode mapear esses campos para `photo_context` / campos novos no JSON (extensão do contrato em ambos os lados).

---

## 9. Diagrama lógico SolidField + watermarker

```
┌─────────────────────────────────────────────────────────────┐
│                    solidfield_core (Django)                  │
│  ┌──────────┐   ┌─────────────┐   ┌──────────────────────┐  │
│  │ orders   │   │ filehub     │   │ apis / checklist     │  │
│  │ WorkOrder│◄──│ WorkOrder   │◄──│ upload metadados     │  │
│  │          │   │ Photo       │   │                      │  │
│  └──────────┘   └──────┬──────┘   └──────────────────────┘  │
│                        │                                      │
│            (integração a implementar)                         │
│                        │ POST webhook + X-Tenant-ID           │
└────────────────────────┼──────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              sf-watermarker-worker-go                         │
│   Gin ──► JetStream ──► Worker ──► JPEG final               │
└─────────────────────────────────────────────────────────────┘
                         │
        alvo SolidField: S3/MinIO + webhook ──► Django (Filehub)
        (hoje no código Go: ainda OUTPUT_DIR local; ver §8.2.1)
```

---

## 10. Variáveis de ambiente (referência)

| Variável | Função |
|----------|--------|
| `OUTPUT_DIR` | Onde gravar `{job_id}.jpg` |
| `PORT` | Porta HTTP (default 8080) |
| `MAX_DIM` | Limite maior lado após resize |
| `GIN_MODE` | Ex.: `release` |
| `NATS_*` | Ver secção 6 |
| `ALLOW_PRIVATE_IPS` | `true` só para dev (SSRF) |

---

## 11. Documentação relacionada neste repositório

- **`README.md`** — como correr NATS, build com/sem HEIF, exemplos `curl`.
- **`GUIA_PROXIMOS_PASSOS_FILEHUB_WATERMARKER.md`** — guia Django + decisão object storage + webhook.
- **`BRIEFING_PARA_FILEHUB_PESCA_MVP.md`** — briefing Filehub / pesca MVP.

---

## 12. Resumo executivo

| Pergunta | Resposta |
|----------|----------|
| O que é? | Microsserviço Go: webhook → fila NATS → worker → JPEG em disco. |
| Para quê? | Marca d’água e metadados de campo sem sobrecarregar o Django. |
| Liga-se ao Filehub? | **Semanticamente sim** (campos equivalentes); **tecnicamente ainda não** no código do core — falta orquestração, persistência do `job_id` e **entrega do ficheiro final** de volta ao storage do SolidField. |
| O que o core deve fazer a seguir? | **Fluxo A adoptado:** implementar webhook Django + extensão do worker para **S3 + callback**; contrato de segurança mútua; actualizar `WorkOrderPhoto` de forma idempotente. |

---

*Documento mantido junto ao código do **sf-watermarker-worker-go**. Actualizar quando existir integração real no **solidfield_core** (paths de código, campos novos, callbacks).*
