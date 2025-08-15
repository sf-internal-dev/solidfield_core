# clients/address_utils.py
import re
from typing import Optional
from django.core.exceptions import ValidationError
from backend.common.address_values import US_STATES, CA_PROVINCES

# --- POSTAL/ZIP validators (boolean) ---
def validate_postal_code(code: Optional[str], country: str) -> bool:
    if not code:
        return False

    if country == "US":
        return bool(re.fullmatch(r"\d{5}(-\d{4})?", code))  # 12345 or 12345-6789
    if country == "CA":
        # A1A 1A1 (allow with/without space)
        return bool(re.fullmatch(r"[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z]\s?\d[ABCEGHJ-NPRSTV-Z]\d", code))
    if country == "UK":
        # UK postcodes are gnarly; this covers common patterns incl. GIR 0AA
        return bool(re.fullmatch(r"(GIR 0AA)|((([A-Z]{1,2}\d[A-Z\d]?)\s?\d[ABD-HJLN-UW-Z]{2}))", code))
    if country == "IE":
        # Eircode: A65 F4E2 (routing key 3 chars + space + unique id 4 chars)
        return bool(re.fullmatch(r"[AC-FHKNPRTV-Y]\d[\w]\s?\w{4}", code))

    return False

# --- state/province validation (boolean) ---
def validate_region_code(state: Optional[str], country: str) -> bool:
    if not state:
        return False

    if country == "US":
        return state in US_STATES
    if country == "CA":
        return state in CA_PROVINCES
   
    if country in ("UK", "IE"):
        # Basic sanity for counties/regions: 2–40 chars, letters/space/hyphen
        return bool(re.fullmatch(r"[A-Z][A-Z \-]{1,39}", state))
    return False

# --- coordinate sanity (boolean) ---
def validate_coordinates(lat: Optional[float], lng: Optional[float]) -> bool:
    if lat is None or lng is None:
        return True  # coordinates are optional
    return -90.0 <= float(lat) <= 90.0 and -180.0 <= float(lng) <= 180.0
