from typing import Optional, Any, List
from backend.apps.checklist.types import NUMERIC_TYPES

# -> Returns True if the template is global.
# Needed when you must branch logic based on global vs scoped templates.
def is_template_global(template) -> bool:
    return bool(template.is_global)

# =========================
# ChecklistItemTemplate utils
# =========================

# -> Returns True if the item is a boolean (yes/no) field.
# Needed when rendering a boolean UI or validating boolean-like answers.
def is_boolean_item(item) -> bool:
    return item.answer_type == "bool"

def is_text_item(item) -> bool:
    return item.answer_type == "text"

def is_number_item(item) -> bool:
    return item.answer_type in NUMERIC_TYPES

def is_choice_item(item) -> bool:
    return item.answer_type == "choice"
# -> Returns True if the item is required.
# Needed when checking whether an answer must be provided.
def is_required_item(item) -> bool:
    return bool(item.required)



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


# -> Returns a human-readable unit symbol for the item's answer type, if any.
# Needed when displaying measurements or formatting answers with units.
def unit_for_item(item) -> Optional[str]:
    mapping = {
        # General
        "number": None,  # Generic number has no fixed unit

        # Angles
        "degree": "°",

        # Metric
        "length_cm": "cm",
        "width_cm": "cm",
        "height_cm": "cm",
        "area_m2": "m²",
        "volume_l": "L",
        "weight_kg": "kg",

        # Imperial
        "length_in": "in",
        "width_in": "in",
        "height_in": "in",
        "area_ft2": "ft²",
        "volume_gal": "gal",
        "weight_lb": "lb",

        # Electrical
        "voltage": "V",
        "current_amp": "A",
        "frequency_hz": "Hz",
        "power_w": "W",
        "power_kw": "kW",

        # Environmental
        "temperature": "°C",
        "temperature_f": "°F",
        "pressure": "psi/bar",
        "humidity_pct": "%",
        "speed_kmh": "km/h",
        "speed_mph": "mph",
    }

    return mapping.get(item.answer_type)




# -> Returns True if the 'order' value is unique within the item's template.
# Needed to keep a strict, non-conflicting step sequence inside one template.
# Note: 'order' is the positional sequence (1, 2, 3, ...) of the question in the checklist.
def has_unique_order_within_template(item) -> bool:
    if not item.pk:
        return not item.template.itens.filter(order=item.order).exists()
    return not item.template.itens.exclude(pk=item.pk).filter(order=item.order).exists()

# -> Returns the next available order number within a template (max(order)+1).
# Needed when auto-assigning the sequence for a newly created item.
def next_order_for_template(template) -> int:
    last = template.itens.order_by("-order").values_list("order", flat=True).first()
    return (last or 0) + 1



