# validators/client_feedback_validators.py
from typing import List, Dict, Any
import re

def validate_client_feedback_payload(payload: Dict[str, Any]) -> List[str]:
    """
    Validate the input payload for creating/updating a ClientFeedback object.
    Validation is field-level only, does not check cross-relations or DB existence.

    Rules:
      - service_order: required (must be present in payload, no type check here)
      - client: optional (not validated here)
      - client_name: max length = 200 chars
      - client_email: optional, must follow basic email format if provided
      - stars: required, integer between 1 and 5
      - comment: optional, must be a string if present
      - strengths: optional, must be a string if present

    Error codes returned:
      - "service_order_required"
      - "client_name_too_long"
      - "client_email_invalid"
      - "stars_required"
      - "stars_not_integer"
      - "stars_out_of_range"
      - "comment_not_string"
      - "strengths_not_string"

    Args:
        payload (Dict[str, Any]): Raw data to be validated, usually from request body.

    Returns:
        List[str]: A list of error codes. Empty list means payload is valid.
    """
    errors: List[str] = []

    # --- service_order ---
    if not payload.get("service_order"):
        errors.append("service_order_required")

    # --- client_name ---
    name = payload.get("client_name", "")
    if name and len(name) > 200:
        errors.append("client_name_too_long")

    # --- client_email ---
    email = payload.get("client_email", "")
    if email:
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, email):
            errors.append("client_email_invalid")

    # --- stars ---
    stars = payload.get("stars")
    if stars is None:
        errors.append("stars_required")
    else:
        try:
            stars_int = int(stars)
            if stars_int < 1 or stars_int > 5:
                errors.append("stars_out_of_range")
        except (ValueError, TypeError):
            errors.append("stars_not_integer")

    # --- comment / strengths ---
    if "comment" in payload and not isinstance(payload["comment"], str):
        errors.append("comment_not_string")
    if "strengths" in payload and not isinstance(payload["strengths"], str):
        errors.append("strengths_not_string")

    return errors
