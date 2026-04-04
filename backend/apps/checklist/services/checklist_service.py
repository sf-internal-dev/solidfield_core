from __future__ import annotations
from backend.apps.checklist.utils.checklist_util import expected_field_for_type, has_required_value, choice_in_options
from backend.apps.checklist.models.checklist import Checklist, ChecklistItemAnswer, ChecklistItemTemplate, ChecklistTemplate
from backend.apps.core.models.technician import Technician
from backend.apps.orders.models import WorkOrder
from typing import Optional, List, Tuple, Dict, Any, Iterable
from django.db import transaction
from backend.apps.core.services.technician_permission_service import has_permission


def create_checklist(
    *,
    technician_operating: Technician,
    template: Optional[ChecklistTemplate],
    filled_by: Optional[Technician] = None,
    work_order: Optional[WorkOrder] = None,
) -> Tuple[Optional[Checklist], List[str]]:
    errors: List[str] = []
    if template is None:
        return None, ["template_required"]

    ok, perm_errors = has_permission(technician_operating, "submit_checklist")
    if not ok:
        return None, perm_errors

    if template.tenant_id != technician_operating.tenant_id:
        return None, ["template_tenant_mismatch"]

    actor = filled_by or technician_operating
    if actor.tenant_id != technician_operating.tenant_id:
        return None, ["filled_by_tenant_mismatch"]

    if work_order is not None and work_order.tenant_id != technician_operating.tenant_id:
        return None, ["work_order_tenant_mismatch"]

    checklist = Checklist.objects.create(
        template=template,
        filled_by=actor,
        work_order=work_order,
        status="draft",
        incomplete=True,
    )
    return checklist, errors

#-> Saves or updates a single checklist item answer for a given checklist
# Determines the correct answer_* field based on the item's answer_type
# Validates required field rules and choice option membership before saving
# Updates existing answers, preserving only the expected field and note if provided
@transaction.atomic
def save_answer(*, technician_operating: Technician, checklist: Checklist, item_template: ChecklistItemTemplate, value: Any, note: str = "",
    ) -> Tuple[Optional[ChecklistItemAnswer], List[str]]:

    errors: List[str] = []

    ok, perm_errors = has_permission(technician_operating, "save_answer")
    if not ok:
        errors.extend(perm_errors)
        return None, errors

    atype = item_template.answer_type
    field = expected_field_for_type(atype)  # "answer_bool" | "answer_texto" | "answer_number" | "answer_choice" | None


    vals = {"answer_bool": None, "answer_texto": None, "answer_number": None, "answer_choice": None}
    if field is not None:
        vals[field] = value

    if not has_required_value(atype, item_template.required, vals):
        errors.append("required_value_missing")
        return None, errors

    if atype == "choice" and not choice_in_options(vals["answer_choice"], item_template.choice_options):
        errors.append("choice_not_in_options")
        return None, errors

    ans, created = ChecklistItemAnswer.objects.get_or_create(
        checklist=checklist,
        item_template=item_template,
        defaults={**vals, "note": note or ""},
    )
    if not created:
        ans.answer_bool = vals["answer_bool"]
        ans.answer_texto = vals["answer_texto"]
        ans.answer_number = vals["answer_number"]
        ans.answer_choice = vals["answer_choice"]
        if note is not None:
            ans.note = note
        ans.save(update_fields=["answer_bool", "answer_texto", "answer_number", "answer_choice", "note"])

    return ans, errors

# -> Deletes a checklist item answer from a given checklist
# Locates the answer by checklist and item_template, returning an error if not found
# Returns a success flag and any error messages
@transaction.atomic
def remove_answer(*, technician_operating: Technician, checklist: Checklist, item_template: ChecklistItemTemplate) -> Tuple[bool, List[str]]:

    errors: List[str] = []

    ok, perm_errors = has_permission(technician_operating, "remove_answer")
    if not ok:
        errors.extend(perm_errors)
        return False, errors

    obj = ChecklistItemAnswer.objects.filter(
        checklist=checklist, item_template=item_template
    ).first()
    if not obj:
        return False, ["item_answer_not_found"]
    obj.delete()
    return True, errors

# -> Identifies required checklist items that have not been answered
# Compares checklist template items against existing answers
# Returns a list of item_template IDs that are missing valid required values
def list_missing_required_answers(*, checklist: Checklist) -> Tuple[List[int], List[str]]:

    errors: List[str] = []

    answers = {
        a.item_template_id: a
        for a in ChecklistItemAnswer.objects.filter(checklist=checklist)
    }

    missing: List[int] = []
    for it in ChecklistItemTemplate.objects.filter(template=checklist.template):
        if not it.required:
            continue

        a = answers.get(it.id)
        vals = {
            "answer_bool":   getattr(a, "answer_bool", None) if a else None,
            "answer_texto":  getattr(a, "answer_texto", None) if a else None,
            "answer_number": getattr(a, "answer_number", None) if a else None,
            "answer_choice": getattr(a, "answer_choice", None) if a else None,
        }
        if not has_required_value(it.answer_type, True, vals):
            missing.append(it.id)

    return missing, errors

# -> Saves multiple checklist item answers in a single transaction
# Accepts a list of payloads containing item_template references, values, and notes
# Resolves item_template IDs to objects and validates each before saving via save_answer
# Returns a list of successfully saved answers and any accumulated validation errors
@transaction.atomic
def bulk_save_answers(
    *,
    technician_operating: Technician,
    checklist: Checklist,
    payloads: Iterable[Dict[str, Any]],
) -> Tuple[List[ChecklistItemAnswer], List[str]]:

    errors: List[str] = []
    saved: List[ChecklistItemAnswer] = []

    def _resolve_item(it_or_id: Any) -> Optional[ChecklistItemTemplate]:
        if isinstance(it_or_id, ChecklistItemTemplate):
            return it_or_id
        try:
            return ChecklistItemTemplate.objects.get(pk=it_or_id)
        except ChecklistItemTemplate.DoesNotExist:
            return None

    for p in payloads:
        it = _resolve_item(p.get("item_template"))
        if not it:
            errors.append("item_template_not_found")
            continue

        ans, errs = save_answer(
            technician_operating=technician_operating,
            checklist=checklist,
            item_template=it,
            value=p.get("value"),
            note=p.get("note") or "",
        )
        if errs:
            errors.extend(errs)
        if ans:
            saved.append(ans)

    return saved, errors

# -> Lists checklists with optional filtering by technician, template, or work order
# Supports pagination and ordering
# Returns a list of checklists with basic information
def list_checklists(*, technician_operating: Technician, technician_id: Optional[int] = None, 
                   template_id: Optional[int] = None, work_order_id: Optional[int] = None,
                   status: Optional[str] = None, limit: int = 50, offset: int = 0) -> Tuple[List[Checklist], List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "view_checklists")
    if not ok:
        return [], perm_errors
    
    # Build query
    queryset = Checklist.objects.filter(template__tenant=technician_operating.tenant)
    
    # Apply filters
    if technician_id:
        queryset = queryset.filter(filled_by_id=technician_id)
    if template_id:
        queryset = queryset.filter(template_id=template_id)
    if work_order_id:
        queryset = queryset.filter(work_order_id=work_order_id)
    if status:
        queryset = queryset.filter(status=status)
    
    # Apply pagination and ordering
    checklists = list(queryset.order_by('-created_at')[offset:offset + limit])
    
    return checklists, errors

# -> Retrieves a specific checklist with all its answers
# Returns detailed checklist information including template and answers
def get_checklist(*, technician_operating: Technician, checklist_id: int) -> Tuple[Optional[Checklist], List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "view_checklists")
    if not ok:
        return None, perm_errors
    
    try:
        checklist = Checklist.objects.select_related('template', 'filled_by', 'work_order').get(
            id=checklist_id,
            template__tenant=technician_operating.tenant
        )
    except Checklist.DoesNotExist:
        return None, ["checklist_not_found"]
    
    return checklist, errors

# -> Submits a checklist for final review/completion
# Validates that all required answers are present
# Updates checklist status to submitted
@transaction.atomic
def submit_checklist(*, technician_operating: Technician, checklist_id: int) -> Tuple[bool, List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "submit_checklist")
    if not ok:
        return False, perm_errors
    
    try:
        checklist = Checklist.objects.get(
            id=checklist_id,
            template__tenant=technician_operating.tenant
        )
    except Checklist.DoesNotExist:
        return False, ["checklist_not_found"]
    
    # Check if already submitted
    if checklist.status == "submitted":
        return False, ["checklist_already_submitted"]
    
    # Validate all required answers are present
    missing_required, missing_errors = list_missing_required_answers(checklist=checklist)
    if missing_required:
        errors.append("missing_required_answers")
        errors.extend(missing_errors)
        return False, errors
    
    checklist.status = "submitted"
    checklist.incomplete = False
    checklist.save(update_fields=["status", "incomplete"])

    return True, errors

# -> Calculates progress statistics for a checklist
# Returns completion percentage, answered items count, and missing required items
def get_checklist_progress(*, technician_operating: Technician, checklist_id: int) -> Tuple[Optional[Dict], List[str]]:
    errors = []
    
    # Check permission
    ok, perm_errors = has_permission(technician_operating, "view_checklists")
    if not ok:
        return None, perm_errors
    
    try:
        checklist = Checklist.objects.get(
            id=checklist_id,
            template__tenant=technician_operating.tenant
        )
    except Checklist.DoesNotExist:
        return None, ["checklist_not_found"]
    
    # Get template items
    template_items = ChecklistItemTemplate.objects.filter(template=checklist.template)
    total_items = template_items.count()
    required_items = template_items.filter(required=True).count()
    
    # Get answered items
    answered_items = ChecklistItemAnswer.objects.filter(checklist=checklist).count()
    
    # Get missing required items
    missing_required, _ = list_missing_required_answers(checklist=checklist)
    missing_count = len(missing_required)
    
    # Calculate progress
    progress_percentage = (answered_items / total_items * 100) if total_items > 0 else 0
    required_progress = ((required_items - missing_count) / required_items * 100) if required_items > 0 else 100
    
    # Get answers with details
    answers = ChecklistItemAnswer.objects.filter(checklist=checklist).select_related('item_template')
    answers_data = []
    for answer in answers:
        answers_data.append({
            "id": answer.id,
            "item_template_id": answer.item_template.id,
            "question": answer.item_template.question,
            "answer_type": answer.item_template.answer_type,
            "required": answer.item_template.required,
            "answer_bool": answer.answer_bool,
            "answer_texto": answer.answer_texto,
            "answer_number": answer.answer_number,
            "answer_choice": answer.answer_choice,
            "note": answer.note,
            "created_at": answer.created_at.isoformat(),
            "updated_at": answer.updated_at.isoformat()
        })
    
    progress_data = {
        "checklist_id": checklist.id,
        "template_name": checklist.template.name,
        "status": checklist.status,
        "total_items": total_items,
        "required_items": required_items,
        "answered_items": answered_items,
        "missing_required_items": missing_count,
        "progress_percentage": round(progress_percentage, 2),
        "required_progress_percentage": round(required_progress, 2),
        "is_complete": missing_count == 0 and required_items > 0,
        "can_submit": missing_count == 0 and required_items > 0,
        "answers": answers_data,
        "missing_required_item_ids": missing_required
    }
    
    return progress_data, errors
