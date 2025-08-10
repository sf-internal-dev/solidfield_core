# clients/address_utils.py
import re
from typing import Optional
from django.core.exceptions import ValidationError

# --- canonical state/province codes (minimal & practical) ---
US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI",
    "MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX",
    "UT","VT","VA","WA","WV","WI","WY","DC"
}
CA_PROVINCES = {"AB","BC","MB","NB","NL","NS","NT","NU","ON","PE","QC","SK","YT"}

# --- POSTAL/ZIP validators (boolean) ---
def validate_postal_code(code: Optional[str], country: str) -> bool:
    if not code:
        return False
    c = country.upper()
    s = code.strip().upper().replace("  ", " ")

    if c == "US":
        return bool(re.fullmatch(r"\d{5}(-\d{4})?", s))  # 12345 or 12345-6789
    if c == "CA":
        # A1A 1A1 (allow with/without space)
        return bool(re.fullmatch(r"[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z]\s?\d[ABCEGHJ-NPRSTV-Z]\d", s))
    if c == "UK":
        # UK postcodes are gnarly; this covers common patterns incl. GIR 0AA
        return bool(re.fullmatch(r"(GIR 0AA)|((([A-Z]{1,2}\d[A-Z\d]?)\s?\d[ABD-HJLN-UW-Z]{2}))", s))
    if c == "IE":
        # Eircode: A65 F4E2 (routing key 3 chars + space + unique id 4 chars)
        return bool(re.fullmatch(r"[AC-FHKNPRTV-Y]\d[\w]\s?\w{4}", s))

    return False

# --- state/province validation (boolean) ---
def validate_region_code(state: Optional[str], country: str) -> bool:
    if not state:
        return False
    s = state.strip().upper()
    c = country.upper()

    if c == "US":
        return s in US_STATES
    if c == "CA":
        return s in CA_PROVINCES
   
    if c in ("UK", "IE"):
        # Basic sanity for counties/regions: 2–40 chars, letters/space/hyphen
        return bool(re.fullmatch(r"[A-Z][A-Z \-]{1,39}", s))
    return False

# --- coordinate sanity (boolean) ---
def validate_coordinates(lat: Optional[float], lng: Optional[float]) -> bool:
    if lat is None or lng is None:
        return True  # coordinates are optional
    return -90.0 <= float(lat) <= 90.0 and -180.0 <= float(lng) <= 180.0


# --- one-shot validator raising ValidationError (use in forms/services) ---
def validate_address_fields(*, country: str, state: str, zip_code: str,
                            city: str, street: str, number: str,
                            gps_latitude: Optional[float] = None,
                            gps_longitude: Optional[float] = None) -> None:
    if not street or not number or not city:
        raise ValidationError("Street, number and city are required.")
    if not validate_region_code(state, country):
        raise ValidationError(f"Invalid state/province for {country}: {state!r}")
    if not validate_postal_code(zip_code, country):
        raise ValidationError(f"Invalid postal/ZIP code for {country}: {zip_code!r}")
    if not validate_coordinates(gps_latitude, gps_longitude):
        raise ValidationError("Invalid latitude/longitude range.")

# --- formatting (for UI/logs) ---
def format_address_line(street: str, number: str, complement: str = "") -> str:
    base = f"{street}, {number}"
    return f"{base} - {complement}".strip(" -")

def format_city_state_postal(city: str, state: str, zip_code: str, country: str) -> str:
    return f"{city} - {state}, {zip_code, country}"

def format_full_address(*, street: str, number: str, complement: str, neighborhood: str,
                        city: str, state: str, zip_code: str, country: str) -> str:
    line1 = format_address_line(street, number, complement)
    line2 = ", ".join(x for x in [neighborhood.strip(), format_city_state_postal(city, state, zip_code, country)] if x)
    return f"{line1}\n{line2}"
