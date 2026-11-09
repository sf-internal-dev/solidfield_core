# validators/checklist_validators.py
import re
from typing import Tuple, List, Optional, Dict, Any, Iterable
from backend.common.helpers.validators import _is_boolish, _only_printable_no_ctrl, _is_positive_int, _split_choice_options

# -----------------------------
# ChecklistTemplate (form)
# -----------------------------

# -> Validates payload for creating/updating a ChecklistTemplate (field-level only)
# Checks: name (1..150, no control chars), service_type (1..100, no control chars),
#         is_active/is_global must be bool-ish, aggroupments as optional list[int]
def validate_checklist_template_payload(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    # name
    name = (payload.get("name") or "").strip()
    if not (1 <= len(name) <= 150):
        errors.append("invalid_template_name_length")
    elif not _only_printable_no_ctrl(name):
        errors.append("invalid_template_name_chars")

    # service_type
    st = (payload.get("service_type") or "").strip()
    if not (1 <= len(st) <= 100):
        errors.append("invalid_service_type_length")
    elif not _only_printable_no_ctrl(st):
        errors.append("invalid_service_type_chars")

    # is_active / is_global (accepts bool or a bool-ish string)
    if "is_active" in payload and not _is_boolish(payload.get("is_active")):
        errors.append("invalid_is_active_type")
    if "is_global" in payload and not _is_boolish(payload.get("is_global")):
        errors.append("invalid_is_global_type")

    # aggroupments (list of positive ids) — does NOT check existence in the DB
    ags = payload.get("aggroupments")
    if ags is not None:
        if not isinstance(ags, (list, tuple)):
            errors.append("invalid_aggroupments_type")
        else:
            for x in ags:
                if not _is_positive_int(x):
                    errors.append("invalid_aggroupment_id")
                    break

    # version is managed by the service; if it comes on the form and you want to check the format:
    if "version" in payload and not _is_positive_int(payload.get("version")):
        errors.append("invalid_version_value")

    return (len(errors) == 0), errors
# -----------------------------
# ChecklistItemTemplate (form)
# -----------------------------

# -> Validates payload for ChecklistItemTemplate (field-level only)
# Checks: order positive int (if provided), question (1..300, no control chars),
#         answer_type within allowed choices, required must be bool-ish,
#         choice_options: lines/CSV, each option <=100 chars (compatible with answer_choice)
def validate_checklist_item_template_payload(
    payload: Dict[str, Any],
    *,
    allowed_answer_types: Iterable[str],
) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    # order (optional; if absent, the service calculates it)
    if "order" in payload and not _is_positive_int(payload.get("order")):
        errors.append("invalid_order_value")

    # question
    q = (payload.get("question") or "").strip()
    if not (1 <= len(q) <= 300):
        errors.append("invalid_question_length")
    elif not _only_printable_no_ctrl(q):
        errors.append("invalid_question_chars")

    # answer_type
    at = payload.get("answer_type")
    allowed = set(allowed_answer_types or [])
    if at not in allowed:
        errors.append("invalid_answer_type")

    # required
    if "required" in payload and not _is_boolish(payload.get("required")):
        errors.append("invalid_required_type")

    # choice_options (format)
    if at == "choice":
        opts = _split_choice_options(payload.get("choice_options"))
        if not opts:
            errors.append("empty_choice_options")
        else:
            for o in opts:
                if len(o) > 100:
                    errors.append("choice_option_too_long")
                    break
                if not _only_printable_no_ctrl(o):
                    errors.append("invalid_choice_option_chars")
                    break

    return (len(errors) == 0), errors

# -----------------------------
# ChecklistItemAnswer (form)
# -----------------------------

# -> Validates raw answer payload shape for a ChecklistItemAnswer (no business rules)
# Required rules / choice-membership must be validated elsewhere; here we only check type/format:
# - answer_type: 'bool' → accepts bool or "true/false/1/0"
# - 'text' → string (no control chars)
# - 'number' and other numeric types → int/float (or numeric string)
# - 'choice' → string (<=100, no control chars) — does NOT validate membership within options
def validate_checklist_item_answer_payload(
    *,
    answer_type: str,
    value: Any,
    note: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    # value format per type (no required rule here)
    if answer_type == "bool":
        if not _is_boolish(value):
            errors.append("invalid_bool_value")

    elif answer_type == "text":
        if not isinstance(value, str):
            errors.append("invalid_text_value")
        else:
            if not _only_printable_no_ctrl(value):
                errors.append("invalid_text_chars")

    elif answer_type == "choice":
        if not isinstance(value, str) or not value.strip():
            errors.append("invalid_choice_value")
        else:
            if len(value) > 100:
                errors.append("choice_value_too_long")
            if not _only_printable_no_ctrl(value):
                errors.append("invalid_choice_chars")

    else:
        # treats all numeric values and measurements as number-like
        if isinstance(value, (int, float)):
            pass
        elif isinstance(value, str):
            try:
                float(value.strip())
            except Exception:
                errors.append("invalid_number_value")
        else:
            errors.append("invalid_number_value")

    # note (optional; only blocks control characters)
    if note is not None and isinstance(note, str) and not _only_printable_no_ctrl(note):
        errors.append("invalid_note_chars")

    return (len(errors) == 0), errors
