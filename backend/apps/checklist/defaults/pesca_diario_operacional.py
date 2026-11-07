"""
Default template: daily operational log for industrial fishing (diesel, ice, temperature).

Numeric types used here must exist in `backend.common.number_codecs.NUMERIC_CODECS`
for consistent validation in `save_answer` (types `volume_l`, `weight_kg`, `temperature`).
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


TEMPLATE_NAME = "Daily Operational Log — Industrial Fishing"
SERVICE_TYPE = "pesca_industrial_diario"

# Fixed order: shift → diesel (consumption/refueling/remaining) → ice → cold room → notes
ITEM_SPECS: List[PescaDiarioItemSpec] = [
    {
        "order": 1,
        "question": "Shift identification (date and period, e.g. 2026-04-03 — morning)",
        "answer_type": "text",
        "required": True,
        "choice_options": "",
    },
    {
        "order": 2,
        "question": "Diesel consumption for the period (liters)",
        "answer_type": "volume_l",
        "required": True,
        "choice_options": "",
    },
    {
        "order": 3,
        "question": "Diesel refueling for the period (liters); enter 0 if there was none",
        "answer_type": "volume_l",
        "required": True,
        "choice_options": "",
    },
    {
        "order": 4,
        "question": "Estimated total diesel on board after the period (liters)",
        "answer_type": "volume_l",
        "required": False,
        "choice_options": "",
    },
    {
        "order": 5,
        "question": "Ice on board — estimated weight (kg)",
        "answer_type": "weight_kg",
        "required": True,
        "choice_options": "",
    },
    {
        "order": 6,
        "question": "Cold room / hold temperature (°C)",
        "answer_type": "temperature",
        "required": True,
        "choice_options": "",
    },
    {
        "order": 7,
        "question": "Operational notes (diesel, ice, or cold room only)",
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
    Creates the v1 template with diesel/ice/temperature items if it does not exist yet
    (same tenant + name + version 1).

    Returns:
        (template, status) — template is None on dry_run when it would be created.
    """
    if created_by.tenant_id != tenant.id:
        raise ValueError("The creating technician must belong to the same tenant.")

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
