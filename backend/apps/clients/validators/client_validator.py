# validators/client_validators.py
import re
from typing import Tuple, List, Optional
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


# -----------------------------
# Client
# -----------------------------

def validate_person_type(value: Optional[str]) -> Tuple[bool, List[str]]:
    if not value:
        return True, []  # permitido em branco
    if value not in ["individual", "company"]:
        return False, ["invalid_person_type"]
    return True, []


def validate_name(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not (1 <= len(s) <= 200):
        return False, ["invalid_name_length"]
    # Aceita letras, números, espaços e alguns sinais básicos
    if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9\s\.\,\-\_]+", s):
        return False, ["invalid_name_charset"]
    return True, []


def validate_document_id(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not s:
        return True, []  # permitido em branco
    if not re.fullmatch(r"[0-9\.\-\/]+", s):
        return False, ["invalid_document_format"]
    if len(s) > 30:
        return False, ["invalid_document_length"]
    return True, []


def validate_contact_name(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not s:
        return True, []
    if len(s) > 100:
        return False, ["invalid_contact_name_length"]
    return True, []


def validate_phone(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not s:
        return True, []
    # Aceita dígitos, +, -, espaço e ()
    if not re.fullmatch(r"[0-9\+\-\(\)\s]+", s):
        return False, ["invalid_phone_format"]
    if len(s) > 30:
        return False, ["invalid_phone_length"]
    return True, []


def validate_email_field(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not s:
        return True, []
    try:
        validate_email(s)
        return True, []
    except ValidationError:
        return False, ["invalid_email"]


# -----------------------------
# ClientAddress
# -----------------------------

def validate_label(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not (1 <= len(s) <= 100):
        return False, ["invalid_label_length"]
    return True, []


def validate_street(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not (1 <= len(s) <= 200):
        return False, ["invalid_street_length"]
    return True, []


def validate_number(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not s:
        return False, ["missing_number"]
    if len(s) > 20:
        return False, ["invalid_number_length"]
    return True, []


def validate_complement(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if len(s) > 100:
        return False, ["invalid_complement_length"]
    return True, []


def validate_neighborhood(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not (1 <= len(s) <= 100):
        return False, ["invalid_neighborhood_length"]
    return True, []


def validate_city(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not (1 <= len(s) <= 100):
        return False, ["invalid_city_length"]
    return True, []


def validate_state(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not (1 <= len(s) <= 50):
        return False, ["invalid_state_length"]
    return True, []


def validate_postal_code(value: Optional[str]) -> Tuple[bool, List[str]]:
    s = (value or "").strip()
    if not s:
        return False, ["missing_postal_code"]
    if len(s) > 20:
        return False, ["invalid_postal_code_length"]
    # Aceita dígitos e hífen (CEP no formato 12345-678 ou simples)
    if not re.fullmatch(r"[0-9\-]+", s):
        return False, ["invalid_postal_code_format"]
    return True, []


def validate_gps_latitude(value: Optional[float]) -> Tuple[bool, List[str]]:
    if value is None:
        return True, []
    if not (-90 <= value <= 90):
        return False, ["invalid_latitude"]
    return True, []


def validate_gps_longitude(value: Optional[float]) -> Tuple[bool, List[str]]:
    if value is None:
        return True, []
    if not (-180 <= value <= 180):
        return False, ["invalid_longitude"]
    return True, []
