# validations/tenant_validators.py
import re
from typing import Tuple, List, Optional

# -> Validates tenant name (required, 1..150)
# Needed to ensure display and DB constraints
def validate_tenant_name(name: Optional[str]) -> Tuple[bool, List[str]]:
    s = (name or "").strip()
    if not s or len(s) > 150:
        return False, ["invalid_tenant_name"]
    return True, []

# -> Validates slug format (lowercase, 1..150, only [a-z0-9-])
# Needed to keep URLs and uniqueness predictable
def validate_slug_format(slug: Optional[str]) -> Tuple[bool, List[str]]:
    s = (slug or "").strip()
    if not s or len(s) > 150:
        return False, ["invalid_slug_length"]
    if not re.fullmatch(r"[a-z0-9-]+", s):
        return False, ["invalid_slug_charset"]
    return True, []

# -> Validates hex color like #RRGGBB
# Needed for UI theming safety
def validate_hex_color(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", s):
        return False, ["invalid_hex_color"]
    return True, []

# -> Validates optional email (accepts empty)
# Needed to avoid noisy email exceptions downstream
def validate_optional_email(email: Optional[str]) -> Tuple[bool, List[str]]:
    if not email:
        return True, []
    # DRF EmailValidator would be better; simple check here:
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
        return False, ["invalid_primary_contact_email"]
    return True, []

# -> Validates optional phone (accepts empty); country-agnostic basic check
def validate_optional_phone(phone: Optional[str]) -> Tuple[bool, List[str]]:
    if not phone:
        return True, []
    s = re.sub(r"\s", "", phone)
    if not re.fullmatch(r"[0-9+().-]{6,30}", s):
        return False, ["invalid_primary_contact_phone"]
    return True, []
