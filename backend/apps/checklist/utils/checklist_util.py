# core/checklists/domain/answer_utils.py
from typing import Optional, Any, Dict, Tuple, List, Set
from backend.apps.checklist.utils.checklist_template_util import unit_for_item, parse_choice_options

# -> Returns which single answer field is expected for this answer_type.
# Needed when deciding which of the four fields ('answer_bool', 'answer_texto', 'answer_number', 'answer_choice')
# should hold the primary value for persistence.
def expected_field_for_type(answer_type: str) -> Optional[str]:
    if answer_type == "bool":
        return "answer_bool"
    if answer_type == "text":
        return "answer_texto"
    if answer_type == "choice":
        return "answer_choice"
    if unit_for_item(answer_type):
        return "answer_number"
    return None  # unknown types fallback (treat elsewhere if needed)

# -> Returns True if a value is present in the appropriate field considering 'required'.
# Needed when enforcing presence rule without raising.
def has_required_value(answer_type: str, required: bool, values: Dict[str, Any]) -> bool:
    if not required:
        return True
    field = expected_field_for_type(answer_type)
    v = values.get(field)
    if field == "answer_bool":
        return v is True or v is False  # must be explicit boolean
    if field == "answer_texto":
        return isinstance(v, str) and v.strip() != ""
    if field == "answer_number":
        return isinstance(v, (int, float))
    if field == "answer_choice":
        return isinstance(v, str) and v.strip() != ""
    return False  # unknown types

# -> Returns True if a choice value exists in allowed options.
# Needed when checking membership for choice fields (case-sensitive by default).
def choice_in_options(choice_value: Optional[str], raw_options: Optional[str]) -> bool:
    if choice_value is None:
        return False
    opts = parse_choice_options(raw_options)
    return choice_value in opts
