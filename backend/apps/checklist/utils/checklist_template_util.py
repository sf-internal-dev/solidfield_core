from typing import Optional, Tuple, List 
from backend.common.number_codecs import NUMERIC_CODECS
from typing import Optional, Any, Dict, Tuple

# -> Parses raw options into a clean, unique, ordered list (comma or newline separated).
# Needed when normalizing the 'choice_options' free-text field into a list of unique options.
def parse_choice_options(raw: Optional[str]) -> List[str]:
    if not raw:
        return []

    parts: List[str] = []
    # Accepts either comma-separated or newline-separated options.
    for chunk in raw.replace(",", "\n").splitlines():
        v = chunk.strip()
        if not v:
            continue
        if v not in parts:
            parts.append(v)
    return parts


def is_numeric_type(answer_type: str) -> bool:
    return answer_type in NUMERIC_CODECS

# -> Returns a human-readable unit symbol for the item's answer type, if any.
# Needed when displaying measurements or formatting answers with units.
def unit_for_type(answer_type: str) -> Optional[str]:
    codec = NUMERIC_CODECS.get(answer_type)
    return codec.canon_unit if codec else None

def parse_number_for_type(answer_type: str, raw_value: Any) -> float:
    """Used on form input → normalizes to the canonical unit and returns a float."""
    codec = NUMERIC_CODECS.get(answer_type)
    if not codec: raise ValueError("not a numeric type")
    return codec.parse(raw_value)

def format_number_for_type(answer_type: str, value_canon: float) -> str:
    """Used on output (display) → formatted string from the canonical value."""
    codec = NUMERIC_CODECS.get(answer_type)
    if not codec: raise ValueError("not a numeric type")
    return codec.fmt(value_canon)

# -> Returns True if the 'order' value is unique within the item's template.
# Needed to keep a strict, non-conflicting step sequence inside one template.
# Note: 'order' is the positional sequence (1, 2, 3, ...) of the question in the checklist.
def has_unique_order_within_template(item) -> Tuple[bool, List[str]]:
    if not item.pk:
        exists = item.template.itens.filter(order=item.order).exists()
    else:
        exists = item.template.itens.exclude(pk=item.pk).filter(order=item.order).exists()
    if exists:
        return False, [f"Order {item.order} already exists in template '{item.template.id}'."]
    return True, []

# -> Returns the next available order number within a template (max(order)+1).
# Needed when auto-assigning the sequence for a newly created item.
def next_order_for_template(template) -> int:
    last = template.itens.order_by("-order").values_list("order", flat=True).first()
    return (last or 0) + 1



