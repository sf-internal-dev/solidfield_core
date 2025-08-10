import re
from typing import Optional

import re
from typing import Optional

def validate_document_id(document_id: Optional[str], country: str) -> bool:
    if not document_id:
        return False

    doc = document_id.strip().upper()
    country = country.upper()

    # ======= 🇺🇸 UNITED STATES =======
    if country == "US":
        # SSN or EIN
        return bool(
            re.fullmatch(r"\d{3}-\d{2}-\d{4}", doc) or  # SSN with dashes
            re.fullmatch(r"\d{9}", doc) or              # SSN without dashes
            re.fullmatch(r"\d{2}-\d{7}", doc)           # EIN
        )

    # ======= 🇨🇦 CANADA =======
    if country == "CA":
        return bool(
            re.fullmatch(r"\d{9}( [A-Z]{2}\d{4})?", doc) or  # BN
            re.fullmatch(r"\d{3}-\d{2}-\d{4}", doc) or       # SIN with dashes
            re.fullmatch(r"\d{9}", doc)                      # SIN without dashes
        )

    # ======= 🇬🇧 UNITED KINGDOM =======
    if country == "UK":
        return bool(
            re.fullmatch(r"[A-Z]{2}\d{6}[A-Z]", doc) or  # NINO
            re.fullmatch(r"\d{8}", doc) or               # CRN (all digits)
            re.fullmatch(r"[A-Z]{2}\d{6}", doc)          # CRN (letters + digits)
        )

    # ======= 🇮🇪 IRELAND =======
    if country == "IE":
        return bool(
            re.fullmatch(r"\d{7}[A-Z]", doc) or           # PPS
            re.fullmatch(r"[A-Z]\d{7}[A-Z]", doc) or      # PPS (letter prefix)
            re.fullmatch(r"\d{6,7}", doc) or              # Company Number (digits)
            re.fullmatch(r"[A-Z]\d{6}", doc)              # Company Number (letter + digits)
        )

    return False


def validate_phone_number(phone_number: Optional[str], country: str) -> bool:
    if not phone_number:
        return False

    s = phone_number.strip()
    c = country.upper()

    # ===== 🇺🇸 UNITED STATES & 🇨🇦 CANADA =====
    # Accept: +1XXXXXXXXXX, (XXX) XXX-XXXX, XXX-XXX-XXXX, XXXXXXXXXX
    if c in ("US", "CA"):
        return bool(
            re.fullmatch(r"\+1\d{10}", s) or
            re.fullmatch(r"\(\d{3}\)\s?\d{3}-\d{4}", s) or
            re.fullmatch(r"\d{3}-\d{3}-\d{4}", s) or
            re.fullmatch(r"\d{10}", s)
        )

    # ===== 🇬🇧 UNITED KINGDOM =====
    # Typical national numbers are 11 digits starting with 0 (e.g., 07… mobiles),
    # and E.164 is +44 followed by 10 digits (national number without leading 0).
    if c == "UK":
        return bool(
            re.fullmatch(r"\+44\d{10}", s) or
            re.fullmatch(r"0\d{10}", s)
        )

    # ===== 🇮🇪 IRELAND =====
    # National significant number is typically 9 digits; with leading 0 it's 10.
    # Accept: +353XXXXXXXXX (9 digits after +353) or 0XXXXXXXXX (10 digits).
    if c == "IE":
        return bool(
            re.fullmatch(r"\+353\d{9}", s) or
            re.fullmatch(r"0\d{9}", s)
        )


    return False
