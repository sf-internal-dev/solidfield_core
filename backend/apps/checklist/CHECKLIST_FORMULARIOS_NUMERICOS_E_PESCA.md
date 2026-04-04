# Formulários versionados, tipos numéricos e diário pesca (diesel / gelo / câmara)

Este documento explica **o que o app `checklist` já oferece** no sentido de *“formulários versionados + tipos numéricos (volume, temperatura, etc.)”* e como isso foi **aplicado ao cenário de pesca industrial**: leituras de **diesel**, **gelo**, **temperatura de câmara** e **registro por turno/dia**.

Documentos relacionados:

- `CHECKLIST_SCHEMA.md` — modelo de domínio, serviços e APIs em geral.
- `defaults/pesca_diario_operacional.py` — definição canônica dos itens do template de pesca.
- `HISTORICO_IMPLEMENTACAO_CHECKLIST_PESCA.md` (raiz do repo) — linha do tempo do que foi implementado e alterado no projeto.

---

## 1. Onde isso vive no código

| Conceito | Onde |
|----------|------|
| Template versionado (nome + versão por tenant) | `models/checklist.py` — `ChecklistTemplate` (`unique_together`: tenant, name, version) |
| Itens do formulário (pergunta, tipo, obrigatoriedade, ordem) | `ChecklistItemTemplate` — campo `answer_type` (choices em `FIELD_TYPE`) |
| Validação de resposta e mapeamento tipo → coluna salva | `utils/checklist_util.py` — `expected_field_for_type`, `has_required_value` |
| Tipos numéricos com unidade / parsing (ex.: L, kg, °C) | `backend/common/number_codecs.py` — `NUMERIC_CODECS` |
| Execução (instância preenchida) | `Checklist` + `ChecklistItemAnswer` |
| Template de pesca pré-definido | `defaults/pesca_diario_operacional.py` |
| Aplicar template v1 no banco | `management/commands/seed_pesca_diario_operacional.py` |

---

## 2. Formulários versionados (o que significa na prática)

- Um **`ChecklistTemplate`** é o “molde” do formulário: possui `name`, `version`, `service_type`, tenant, `is_active`, escopo global ou por grupo (`aggroupments`), etc.
- Várias versões coexistem com o **mesmo nome** desde que a **versão** seja diferente (ex.: v1, v2 após `update_checklist_template_version`).
- Os **`ChecklistItemTemplate`** são as linhas do formulário, com **`order`** fixando a sequência (turno primeiro, depois medições, etc.).
- Cada preenchimento em campo gera um **`Checklist`** (instância) ligado a um template **congelado naquela versão** e opcionalmente a uma **`WorkOrder`** (viagem).  
  Assim, “registro por turno/dia” = **um `Checklist` por turno** (ou por janela operacional), não um template novo a cada dia.

---

## 3. Tipos numéricos (volume, temperatura, massa, etc.)

### 3.1 Tipos declarados no item (`answer_type`)

Em `ChecklistItemTemplate`, `answer_type` usa as choices de `FIELD_TYPE` (trecho relevante para o MVP pesca):

- Medida de **volume**: `volume_l` (litros), entre outros (ex.: `volume_gal`).
- Medida de **massa**: `weight_kg` (quilogramas), entre outros.
- **Temperatura**: `temperature` (°C na pergunta; armazenamento/validação alinhados ao codec).

Há também `number` genérico e dezenas de tipos industriais (elétricos, dimensões, etc.) para outros casos de uso.

### 3.2 Consistência com `NUMERIC_CODECS`

Para o fluxo **`save_answer`** funcionar de forma uniforme, tipos “numéricos especializados” usados em perguntas devem existir em **`NUMERIC_CODECS`** (`number_codecs.py`). Isso garante:

- parse aceitando vírgula decimal (pt-BR) onde aplicável;
- valor persistido de forma coerente no campo **`answer_number`** do `ChecklistItemAnswer` (via `expected_field_for_type` → `"answer_number"`).

Para o template de pesca usamos explicitamente:

- `volume_l` → litros (diesel);
- `weight_kg` → quilogramas (gelo);
- `temperature` → °C (câmara / poço).

### 3.3 Resumo tipo → coluna salva

| `answer_type` (exemplo) | Campo principal na resposta |
|-------------------------|-----------------------------|
| `text` | `answer_texto` |
| `bool` | `answer_bool` |
| `choice` | `answer_choice` |
| `volume_l`, `weight_kg`, `temperature`, `number`, … | `answer_number` |

---

## 4. Aplicação ao MVP pesca: diesel, gelo, temperatura, turno

O arquivo **`defaults/pesca_diario_operacional.py`** define o template **`Diário Operacional — Pesca Industrial`** com `service_type = pesca_industrial_diario` e os itens abaixo.

| Ordem | Finalidade operacional | `answer_type` | Obrigatório |
|------:|------------------------|---------------|-------------|
| 1 | Identificação do **turno** (data + período, ex. manhã) | `text` | Sim |
| 2 | **Consumo** de diesel no período (L) | `volume_l` | Sim |
| 3 | **Abastecimento** de diesel no período (L); 0 se não houve | `volume_l` | Sim |
| 4 | **Estimativa** de diesel total em bordo após o período (L) | `volume_l` | Não |
| 5 | **Gelo** em bordo — peso estimado (kg) | `weight_kg` | Sim |
| 6 | **Temperatura** da câmara fria / poço (°C) | `temperature` | Sim |
| 7 | Observações apenas no escopo diesel / gelo / câmara | `text` | Não |

Assim, a linha da tabela de produto que você citou fica coberta:

> Formulários versionados + tipos numéricos (volume, temperatura, etc.) em `backend/apps/checklist/` para leituras de **diesel**, **gelo**, **temperatura de câmara**, **registros por turno/dia**.

- **Turno/dia**: item 1 (texto) + uma instância de **`Checklist` por preenchimento** (idealmente amarrada à **`WorkOrder`** da viagem — ver APIs no histórico do projeto).
- **Diesel / gelo / temperatura**: itens 2–6 com tipos alinhados a `NUMERIC_CODECS`.

Para **criar o template v1** no banco de um tenant, use:

```bash
python manage.py seed_pesca_diario_operacional --tenant-id <id> --technician-id <id>
```

---

## 5. Versionamento depois da v1

Novas versões do mesmo nome de template podem ser criadas pelo serviço **`update_checklist_template_version`** (copia itens, ajusta remoções/adições, desativa versão anterior conforme parâmetros).  
O seed documentado aqui fixa **apenas a v1** idempotente; evoluções do formulário (campos novos de operação ou compliance) entram como **v2, v3, …** sem perder histórico dos `Checklist` já ligados à v1.

---

## 6. Limitações conscientes

- Nem todo `answer_type` listado em `FIELD_TYPE` está em `NUMERIC_CODECS`; para novos itens numéricos, validar em `checklist_util` / testes antes de usar em produção.
- Observações livres (item 7) dependem de disciplina operacional; regras semânticas mais rígidas estão descritas em `CHECKLIST_SCHEMA.md` (seção de qualidade de texto).
