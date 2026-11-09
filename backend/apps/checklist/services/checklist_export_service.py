"""
Tabular export of checklists and answers for BI / spreadsheets (fishing / operations MVP).
"""

from __future__ import annotations

import csv
from io import StringIO
from typing import List, Optional, Tuple

from backend.apps.checklist.models import Checklist, ChecklistItemAnswer
from backend.apps.core.models.technician import Technician
from backend.apps.core.services.technician_permission_service import has_permission

CSV_HEADER = [
    "checklist_id",
    "status",
    "incomplete",
    "work_order_id",
    "work_order_identifier",
    "template_id",
    "template_name",
    "service_type",
    "filled_by_id",
    "filled_by_username",
    "item_order",
    "question",
    "answer_type",
    "answer_bool",
    "answer_texto",
    "answer_number",
    "answer_choice",
    "note",
    "answer_updated_at",
]


def export_checklist_answers_csv(
    *,
    technician_operating: Technician,
    work_order_id: Optional[int] = None,
    service_type: Optional[str] = None,
    template_id: Optional[int] = None,
) -> Tuple[Optional[str], List[str]]:
    ok, perm_errors = has_permission(technician_operating, "view_checklists")
    if not ok:
        return None, perm_errors

    qs = Checklist.objects.filter(template__tenant_id=technician_operating.tenant_id).select_related(
        "template", "filled_by", "work_order"
    )

    if work_order_id is not None:
        qs = qs.filter(work_order_id=work_order_id)
    if service_type:
        qs = qs.filter(template__service_type=service_type)
    if template_id is not None:
        qs = qs.filter(template_id=template_id)

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_HEADER)

    for cl in qs.order_by("id"):
        wo = cl.work_order
        base_prefix = [
            cl.id,
            cl.status,
            cl.incomplete,
            wo.id if wo else "",
            wo.identifier if wo else "",
            cl.template_id,
            cl.template.name,
            cl.template.service_type,
            cl.filled_by_id,
            cl.filled_by.username,
        ]
        answers = (
            ChecklistItemAnswer.objects.filter(checklist=cl)
            .select_related("item_template")
            .order_by("item_template__order")
        )
        rows = list(answers)
        if not rows:
            writer.writerow(base_prefix + ["", "", "", "", "", "", "", "", ""])
            continue
        for ans in rows:
            it = ans.item_template
            writer.writerow(
                base_prefix
                + [
                    it.order,
                    it.question,
                    it.answer_type,
                    ans.answer_bool,
                    ans.answer_texto,
                    ans.answer_number,
                    ans.answer_choice,
                    ans.note,
                    ans.updated_at.isoformat() if ans.updated_at else "",
                ]
            )

    return buf.getvalue(), []
