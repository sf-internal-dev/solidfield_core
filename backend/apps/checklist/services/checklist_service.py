from backend.apps.checklist.utils.checklist_util import expected_field_for_type, has_required_value, choice_in_options
from backend.apps.checklist.models.checklist import Checklist, ChecklistItemAnswer, ChecklistItemTemplate, ChecklistTemplate
from backend.apps.core.models.technician import Technician
from __future__ import annotations
from typing import Optional, List, Tuple, Dict, Any, Iterable
from django.db import transaction

#-> Creates a new checklist instance for a given template and technician
# Associates the checklist with the provided template and filled_by technician
# Returns the created checklist object along with any validation errors
def create_checklist(*, template: ChecklistTemplate, filled_by: Technician) -> Tuple[Optional[Checklist], List[str]]:
   
    errors: List[str] = []
    checklist = Checklist.objects.create(template=template, filled_by=filled_by)
    return checklist, errors

#-> Saves or updates a single checklist item answer for a given checklist
# Determines the correct answer_* field based on the item's answer_type
# Validates required field rules and choice option membership before saving
# Updates existing answers, preserving only the expected field and note if provided
@transaction.atomic
def save_answer(*, checklist: Checklist, item_template: ChecklistItemTemplate, value: Any, note: str = "",
    ) -> Tuple[Optional[ChecklistItemAnswer], List[str]]:

    errors: List[str] = []

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
def remove_answer(*, checklist: Checklist, item_template: ChecklistItemTemplate) -> Tuple[bool, List[str]]:

    errors: List[str] = []

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
def bulk_save_answers(*,checklist: Checklist, payloads: Iterable[Dict[str, Any]],) -> Tuple[List[ChecklistItemAnswer], List[str]]:

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
