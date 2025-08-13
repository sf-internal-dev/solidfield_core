from typing import Optional, Any, List

# -> Returns True if the template is global.
# Needed when you must branch logic based on global vs scoped templates.
"""Very Important"""
def is_template_global(template) -> bool:
    return bool(template.is_global)


# -> Returns True if the template currently has at least one aggroupment linked.
# Needed when enforcing rules that require at least one group for non-global templates.
"""Secondary"""

def has_any_aggroupment(template) -> bool:
    return template.aggroupments.exists() if template.pk else False


# -> Returns how many aggroupments are linked to the template.
# Needed when you want a quick count to validate or display association totals.
"""Secondary"""
def count_aggroupments(template) -> int:
    return template.aggroupments.count() if template.pk else 0


# -> Returns True if the template can receive aggroupments (i.e., it is not global).
# Needed when deciding whether to allow add/link actions to groups.
"""Very Important"""
def can_attach_aggroupments(template) -> bool:
    return not is_template_global(template)


# -> Returns True if the template is non-global and has at least one aggroupment.
# Needed when checking if a template is effectively scoped by groups.
"""Secondary"""
def is_scoped_to_aggroupments(template) -> bool:
    return not is_template_global(template) and has_any_aggroupment(template)


# -> Returns True if the current state matches the rule:
#    global => 0 groups, non-global => >= 1 group.
# Needed when validating the current persisted state before proceeding.
"""Secondary"""
def aggroupment_count_is_valid(template) -> bool:
    count = count_aggroupments(template)
    return (is_template_global(template) and count == 0) or (
        not is_template_global(template) and count >= 1
    )


# =========================
# ChecklistItemTemplate utils
# =========================

# -> Returns True if the item is a boolean (yes/no) field.
# Needed when rendering a boolean UI or validating boolean-like answers.
"""Very Important"""
def is_boolean_item(item) -> bool:
    return item.answer_type == "bool"


# -> Returns True if the item is a free text field.
# Needed for text input rendering and simple text validation.
"""Very Important"""
def is_text_item(item) -> bool:
    return item.answer_type == "text"


# -> Returns True if the item is a numeric/measurement-like field.
# Needed to drive numeric validation and numeric UI widgets.
"""Very Important"""
def is_number_item(item) -> bool:
    return item.answer_type in {
        "number", "degree",
        # Metric
        "length_cm", "width_cm", "height_cm", "area_m2", "volume_l", "weight_kg",
        # Imperial
        "length_in", "width_in", "height_in", "area_ft2", "volume_gal", "weight_lb",
        # Electrical
        "voltage", "current_amp", "frequency_hz", "power_w", "power_kw",
        # Environmental
        "temperature", "temperature_f", "pressure", "humidity_pct",
        "speed_kmh", "speed_mph"
    }

# -> Returns True if the item is a single-choice field.
# Needed to render/select from predefined options and validate membership.
"""Very Important"""
def is_choice_item(item) -> bool:
    return item.answer_type == "choice"


# -> Returns True if the item is required.
# Needed when checking whether an answer must be provided.
"""Very Important"""
def is_required_item(item) -> bool:
    return bool(item.required)


# -> Parses raw options into a clean, unique, ordered list (comma or newline separated).
# Needed when normalizing the 'choice_options' free-text field into a list of unique options.
"""Very Important"""
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
"""Very Important"""
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


# -> Returns a short label like "1. Question..." truncated to max_len.
# Needed for compact UI listings and summaries of checklist items.
"""Secondary"""
def short_label(item, max_len: int = 40) -> str:
    q = item.question or ""
    trunc = (q[:max_len] + "...") if len(q) > max_len else q
    return f"{item.order}. {trunc}"


# -> Returns True if the 'order' value is unique within the item's template.
# Needed to keep a strict, non-conflicting step sequence inside one template.
# Note: 'order' is the positional sequence (1, 2, 3, ...) of the question in the checklist.
""" Very Important """
def has_unique_order_within_template(item) -> bool:
    if not item.pk:
        return not item.template.itens.filter(order=item.order).exists()
    return not item.template.itens.exclude(pk=item.pk).filter(order=item.order).exists()


# -> Returns the next available order number within a template (max(order)+1).
# Needed when auto-assigning the sequence for a newly created item.
"""Very Important"""
def next_order_for_template(template) -> int:
    last = template.itens.order_by("-order").values_list("order", flat=True).first()
    return (last or 0) + 1


# -> Returns how many items a template currently has.
# Needed for quick counts (dashboards, summaries, or validation).
"""Secondary"""
def items_count(template) -> int:
    return template.itens.count()


# -> Converts a "yes"/"no" string to boolean. Returns None if not recognized.
# Needed when validating boolean answers coming from UI or payloads.
"""Very Important"""
def _to_bool_like(v: Any) -> Optional[bool]:
    return {"yes": True, "no": False}.get(str(v).strip().lower())


# -> Returns True if 'v' can be parsed as a float.
# Needed for validating numeric-like inputs for measurement fields.
"""Very Important"""
def _is_number_like(v: Any) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


# -> Returns True if 'v' is a non-empty string.
# Needed when checking required text fields.
"""Very Important"""
def _is_nonempty_text(v: Any) -> bool:
    return isinstance(v, str) and len(v.strip()) > 0


# -> Normalizes a choice value to a non-empty string or returns None.
# Needed before checking membership against parsed choice options.
"""Very Important"""
def _normalize_choice(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


# -> Returns True if 'value' is compatible with the item's answer type.
# Needed for type-level validation before applying 'required' rules.
"""Very Important"""
def is_valid_answer_for_item(item, value: Any) -> bool:
    if is_boolean_item(item):
        return _to_bool_like(value) is not None

    if is_text_item(item):
        return isinstance(value, str)

    if is_number_item(item):
        return _is_number_like(value)

    if is_choice_item(item):
        opt = _normalize_choice(value)
        return opt in parse_choice_options(getattr(item, "choice_options", ""))

    # Fallback: treat unknown types as text-like.
    return isinstance(value, str)


# -> Returns True if the 'required' rule is satisfied for the given value.
# Needed to confirm presence/format according to each answer type when required=True.
"""Very Important"""
def satisfies_required_rule(item, value: Any) -> bool:
    if not is_required_item(item):
        return True

    if is_boolean_item(item):
        return _to_bool_like(value) is not None

    if is_text_item(item):
        return _is_nonempty_text(value)

    if is_number_item(item):
        return _is_number_like(value)

    if is_choice_item(item):
        opt = _normalize_choice(value)
        return opt in parse_choice_options(getattr(item, "choice_options", ""))

    # Fallback for unknown types: require non-empty text.
    return _is_nonempty_text(value)
