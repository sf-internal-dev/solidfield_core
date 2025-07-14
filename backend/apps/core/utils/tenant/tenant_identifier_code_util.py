import re
from django.utils.crypto import get_random_string
from django.utils.text import slugify
import unicodedata

# -> Generates a list of possible tenant_code attempts based on a slug
# Normalizes and uppercases the input, then returns up to `max_tries` unique codes
# Each code is based on the first 4 valid alphanumeric characters of the slug, with incremental numeric suffixes
# Ex: "solid field" → ["SOLI", "SOLI1", "SOLI2", ..., "SOLI29"]
def generate_tenant_code_attempts(slug: str, max_tries: int = 30) -> list[str]:
    normalized = unicodedata.normalize("NFKD", slug)
    ascii_slug = normalized.encode("ascii", "ignore").decode("ascii")
    base = re.sub(r'[^A-Z0-9]', '', ascii_slug.upper())[:4] or "COMP"
    base = base[:4]

    attempts = []
    for i in range(max_tries):
        suffix = "" if i == 0 else str(i)
        attempt = f"{base}{suffix}"
        attempts.append(attempt)

    return attempts

