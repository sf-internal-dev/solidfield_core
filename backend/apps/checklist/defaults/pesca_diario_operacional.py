"""
Template padrão: diário operacional para pesca industrial (diesel, gelo, temperatura).

Tipos numéricos usados aqui precisam existir em `backend.common.number_codecs.NUMERIC_CODECS`
para validação consistente em `save_answer` (tipos `volume_l`, `weight_kg`, `temperature`).
"""

from __future__ import annotations

from typing import List, Literal, Optional, Tuple, TypedDict

from django.db import transaction

from backend.apps.checklist.models.checklist import ChecklistItemTemplate, ChecklistTemplate
from backend.apps.core.models.technician import Technician


class PescaDiarioItemSpec(TypedDict):
    order: int
    question: str
    answer_type: str
    required: bool
    choice_options: str


TEMPLATE_NAME = "Diário Operacional — Pesca Industrial"
SERVICE_TYPE = "pesca_industrial_diario"

# Ordem fixa: turno → diesel (consumo/abastecimento/remanescente) → gelo → câmara → observações
ITEM_SPECS: List[PescaDiarioItemSpec] = [
    {
        "order": 1,
        "question": "Identificação do turno (data e período, ex.: 2026-04-03 — manhã)",
        "answer_type": "text",
        "required": True,
        "choice_options": "",
    },
    {
        "order": 2,
        "question": "Consumo de diesel no período (litros)",
        "answer_type": "volume_l",
        "required": True,
        "choice_options": "",
    },
    {
        "order": 3,
        "question": "Abastecimento de diesel no período (litros); informe 0 se não houve",
        "answer_type": "volume_l",
        "required": True,
        "choice_options": "",
    },
    {
        "order": 4,
        "question": "Estimativa de diesel total em bordo após o período (litros)",
        "answer_type": "volume_l",
        "required": False,
        "choice_options": "",
    },
    {
        "order": 5,
        "question": "Gelo em bordo — peso estimado (kg)",
        "answer_type": "weight_kg",
        "required": True,
        "choice_options": "",
    },
    {
        "order": 6,
        "question": "Temperatura da câmara fria / poço (°C)",
        "answer_type": "temperature",
        "required": True,
        "choice_options": "",
    },
    {
        "order": 7,
        "question": "Observações operacionais (somente diesel, gelo ou câmara)",
        "answer_type": "text",
        "required": False,
        "choice_options": "",
    },
]

EnsureStatus = Literal["created", "skipped", "would_create"]


def ensure_pesca_diario_operacional_template(
    tenant,
    created_by: Technician,
    *,
    dry_run: bool = False,
) -> Tuple[Optional[ChecklistTemplate], EnsureStatus]:
    """
    Cria o template v1 com itens de diesel/gelo/temperatura, se ainda não existir
    (mesmo tenant + nome + versão 1).

    Returns:
        (template, status) — template é None em dry_run quando seria criado.
    """
    if created_by.tenant_id != tenant.id:
        raise ValueError("O técnico criador deve pertencer ao mesmo tenant.")

    exists = ChecklistTemplate.objects.filter(
        tenant=tenant,
        name=TEMPLATE_NAME,
        version=1,
    ).exists()
    if exists:
        tpl = ChecklistTemplate.objects.get(tenant=tenant, name=TEMPLATE_NAME, version=1)
        return tpl, "skipped"

    if dry_run:
        return None, "would_create"

    with transaction.atomic():
        tpl = ChecklistTemplate.objects.create(
            tenant=tenant,
            name=TEMPLATE_NAME,
            version=1,
            created_by=created_by,
            service_type=SERVICE_TYPE,
            is_active=True,
            is_global=True,
        )
        ChecklistItemTemplate.objects.bulk_create(
            [
                ChecklistItemTemplate(
                    template=tpl,
                    order=spec["order"],
                    question=spec["question"],
                    answer_type=spec["answer_type"],
                    required=spec["required"],
                    choice_options=spec.get("choice_options") or "",
                )
                for spec in ITEM_SPECS
            ]
        )

    return tpl, "created"
