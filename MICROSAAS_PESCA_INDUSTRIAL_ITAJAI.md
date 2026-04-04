# SolidField × Pesca Industrial de Larga Escala (Itajaí/SC)

**Papel:** Engenheiro de Operações e Estrategista de Negócios — cenário armador / frota industrial no hub de Itajaí.

**Objetivo do documento:** mapear a estrutura atual do SolidField (SaaS de operações em campo em tempo real) para um **Micro-SaaS de entrada (MVP)** que ataque a dor com maior impacto econômico imediato para o armador, com **baixo esforço de UI** e **alto valor analítico (Ti)**.

---

## 1. Leitura do SolidField para pesca industrial

O repositório oferece capacidades **reaproveitáveis** (sem assumir módulos que não existem no código):

| Capacidade no código | Onde vive | Uso direto em pesca |
|----------------------|-----------|---------------------|
| Formulários versionados + tipos numéricos (volume, temperatura, etc.) | `backend/apps/checklist/` + seed em `checklist/defaults/pesca_diario_operacional.py` | Leituras de **diesel**, **gelo**, **temperatura de câmara**, registros por turno/dia | feito
| Execução em campo + progresso + submissão | `checklist/services/checklist_service.py` | “Diário” estruturado com regras de obrigatoriedade antes de fechar o dia |
| Fila offline | `backend/apps/core/models/sync.py` (`OfflineSyncQueue`) | Mar sem sinal: enfileira respostas e sincroniza no porto |
| Evidência (foto/assinatura + geo) | `backend/apps/filehub/` | Comprovação de leitura, estado do gelo, lacres, nota de abastecimento |
| Objeto operacional por viagem | `backend/apps/orders/` (`WorkOrder`) | Contêiner lógico: **1 viagem / 1 lote de mar** amarrando checklists e evidências |
| Auditoria + trilha + permissões | `core` + logs | Menos fraude e mais defesa em fiscalização / disputas internas |
| Saída para relatório / PDF | `reporting` + links de download em `orders` | Base para **Mapa de Bordo** ou pacote para órgão (depende do que o `reporting` já gera hoje) |

**O que não está pronto como motor isolável no código atual:**

- Inventário / BOM / estoque formal de peças
- Telemetria automática de motor (CAN bus, sensores)
- **Motor de quinhão** (regras de repasse por captura, tripulação, armador)

Isso seria produto novo ou integração — não bloqueia o MVP recomendado abaixo.

---

## 2. Variáveis críticas do setor × encaixe no SolidField

### 2.1 Gestão de insumos voláteis — Diesel vs. autonomia

- **Encaixe:** checklist com campos numéricos + notas + (opcional) foto de painel/medidor (`filehub`).
- **Valor analítico:** série temporal por viagem; regras simples (consumo/dia vs. estoque declarado, alertas heurísticos).
- **Impacto em caixa:** diesel costuma ser um dos maiores OPEX; erro de planejamento gera custo imediato (tempo de mar inadequado, ida extra ao porto, compra emergencial).

### 2.2 Logística de perecíveis — Gelo, temperatura vs. tempo de mar

- **Encaixe:** tipos de temperatura e medidas no checklist + evidência fotográfica.
- **Impacto em caixa:** perda de produto e gelo “queimado” é dinheiro direto.

### 2.3 Conformidade legal — Mapa de Bordo para órgãos reguladores

- **Encaixe:** template versionado + submissão + auditoria + export/PDF (se `reporting` cobrir; senão MVP = JSON estruturado + CSV e PDF em fase seguinte).
- **Impacto:** multas, retenção, atraso — hemorragia legal e operacional no porto.

### 2.4 Cálculo de quinhão — Divisão de lucros (captura real)

- **Encaixe atual:** **não há** núcleo no repositório; exige modelo de captura (peso, espécie, valor comercializado) + motor de regras.
- **Risco de MVP em 30 dias:** alto — disputa de regras e qualidade dos dados; melhor como fase 2 após diário operacional confiável.

---

## 3. Uma funcionalidade para ~30 dias (MVP Micro-SaaS)

### 3.1 Recomendação única

**Nome de trabalho:** *Diário de Bordo Operacional — Diesel, Gelo e Câmara* (marca comercial à definir).

**Definição:** um **pacote de templates versionados + execução + sincronização offline**, amarrado a uma **“Viagem”** (conceitualmente: `WorkOrder` como viagem ou ciclo de mar), com **API estável e/ou export** para BI/planilha no lugar de UI pesada no lançamento.

### 3.2 Por que esta e não só Mapa de Bordo ou só Quinhão

| Opção | Prós | Contras para 30 dias |
|-------|------|------------------------|
| **Diesel + gelo + câmara** | Encaixa no checklist + offline; economia **imediata** em OPEX variável | Precisa disciplina de preenchimento (mitigável com evidência) |
| **Só Mapa de Bordo** | Alto valor regulatório | Gargalo costuma ser **layout legal + validação com órgão**, não só software |
| **Só Quinhão** | Alto valor societário | Domínio novo; dados de captura/preço; conflito armador/tripulação |

**Prioridade explícita:** maximizar **economia imediata de dinheiro** para o armador → **diesel + gelo/temperatura** primeiro.

**Mapa de Bordo** como **fase 1b ou 2:** mesmo motor (`checklist` + auditoria + reporting), outro template e pipeline de documento oficial.

**Quinhão** após existir **captura comercializada confiável** (peso, espécie, valor, descontos).

---

## 4. Escopo enxuto de 30 dias

1. **Templates (versionados):** blocos para abastecimento/consumo diário de diesel, gelo (estoque estimado ou balança), temperatura de câmara, observações operacionais — alinhado às regras semânticas em `backend/apps/checklist/CHECKLIST_SCHEMA.md` (ex.: não misturar aquisição e contratação em itens de contexto único).
2. **Contexto de viagem:** 1 `WorkOrder` = 1 viagem (ou 1 ciclo mar); checklists e evidências vinculados.
3. **Offline:** uso de `OfflineSyncQueue` para preenchimento no mar.
4. **Saída analítica (Ti alto, UI baixa):** endpoint ou export CSV dos answers agregados por viagem/dia — armador usa Excel, Google Sheets ou Power BI no MVP.
5. **Opcional rápido:** foto de medidor/câmara com geo (`filehub`) para reduzir contestação interna.

---

## 5. Resumo executivo

| Critério | Melhor encaixe no SolidField |
|----------|------------------------------|
| Dor que mais sangra em **caixa operacional** de curto prazo | **Diesel + gelo/temperatura** (dados cabem no checklist) |
| Dor **regulatória** | **Mapa de bordo** (mesmo motor; camada legal/PDF em sequência) |
| Dor **societária / lucro** | **Quinhão** (novo domínio — não priorizar para MVP de 30 dias) |

**MVP único em 30 dias:** Micro-SaaS de **registro operacional estruturado (diesel, gelo, câmara) com offline e analytics via API/export**, usando `checklist` + `WorkOrder` (viagem) + `OfflineSyncQueue` (+ opcional `filehub`) — máximo reaproveitamento do SolidField, mínima UI inicial, máximo retorno analítico e impacto direto no bolso do armador.

---

## 6. Próximos passos sugeridos (fora do escopo deste .md)

- One-pager de produto: ICP (armador / gestor de frota Itajaí), até 3 telas, KPIs Ti, explícito o que **não** entra no MVP.
- OpenAPI estável para os endpoints de checklist/execução usados pelo MVP.
- Validação com 1–2 armadores sobre campos mínimos do diário (diesel/gelo/temperatura) antes de congelar templates v1.

---

## 7. Implementação no repositório (primeira parte — template checklist)

Foi adicionado um **template versionado v1** com itens alinhados ao MVP (diesel em litros, gelo em kg, temperatura da câmara em °C, turno em texto e observações restritas ao escopo operacional).

### 7.1 Onde está no código

- Definição dos itens e função idempotente: `backend/apps/checklist/defaults/pesca_diario_operacional.py`
- Comando Django (por tenant): `backend/apps/checklist/management/commands/seed_pesca_diario_operacional.py`

Constantes úteis:

- Nome do template: `Diário Operacional — Pesca Industrial`
- `service_type`: `pesca_industrial_diario`

### 7.2 Como aplicar

Na raiz do projeto (com venv ativo, se usar):

```bash
cd /home/adryan/solidfield_core
python manage.py seed_pesca_diario_operacional --dry-run
python manage.py seed_pesca_diario_operacional --tenant-id 1 --technician-id 1
```

- Se `--tenant-id` for omitido, o comando usa o **primeiro** `CompanyTenant` ativo.
- Se `--technician-id` for omitido, usa o **primeiro** `Technician` ativo daquele tenant (como `created_by` do template).
- Se o template **v1** com esse nome já existir para o tenant, o comando **não altera** nada (idempotente).

### 7.3 Vínculo com viagem e export (implementado)

- **Criar checklist com viagem:** `POST /create_checklist_api/` com JSON `template`, opcional `work_order` (ID da `WorkOrder` do mesmo tenant), opcional `filled_by` (senão usa o técnico da sessão).
- **Export CSV para BI:** `GET /export_checklist_answers_csv_api/` com query opcional `work_order_id`, `service_type` (ex.: `pesca_industrial_diario`), `template_id`. Resposta: arquivo CSV (UTF-8 com BOM para Excel).

### 7.4 Próximo passo de produto (opcional)

- Opcional: itens de evidência (`filehub`) para foto do medidor / termômetro.
- Dashboard dedicado ou agendamento de relatórios (hoje: download manual do CSV).
