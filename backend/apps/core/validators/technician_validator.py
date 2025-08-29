# validators/technician_validators.py
import re
from typing import Tuple, List, Optional, Dict, Any

# -----------------------------
# Field-level validators
# -----------------------------

# -> Validates username format (1..32 chars, lowercase letters/_/- only, no digits)
# Needed to ensure usernames are clean, predictable handles
def validate_username(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not (1 <= len(s) <= 32):
        return False, ["invalid_username_length"]
    if not re.fullmatch(r"[a-z_-]+", s):
        return False, ["invalid_username_charset"]
    return True, []

# -> Validates social_name (1..150 chars, only letters + spaces)
# Needed to enforce proper human-like display names (e.g. "John Carl Smith")
def validate_social_name(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not (1 <= len(s) <= 150):
        return False, ["invalid_social_name_length"]
    if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ ]+", s):
        return False, ["invalid_social_name_chars"]

    return True, []

# -> Validates technician_permission is one of allowed choices
# Needed to guard basic enum input (business meaning is handled elsewhere)
def validate_technician_permission(value: Optional[str], allowed=("L1", "L2", "L3")) -> Tuple[bool, List[str]]:
    if (value or "") in allowed:
        return True, []
    return False, ["invalid_permission_choice"]

# -> Validates is_active is a proper boolean (or boolean-like string)
# Needed when forms may send strings; convert upstream if desired
def validate_is_active(value: Any) -> Tuple[bool, List[str]]:
    if isinstance(value, bool):
        return True, []
    if isinstance(value, str) and value.strip().lower() in ("true", "false", "1", "0"):
        return True, []  # tipagem/conversão pode ser feita no serializer
    return False, ["invalid_is_active_type"]