import re
import unicodedata

# -> Sanitizes a slug by removing accents, special characters, and non-ASCII symbols
# Converts the string to lowercase and keeps only a-z and 0-9 characters
# Ex: "Sóli-d.f!eld" → "soliddfeld"
def sanitize_tenant_slug(slug: str) -> str:
    normalized = unicodedata.normalize("NFKD", slug)
    ascii_slug = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_slug = ascii_slug.lower()
    sanitized = re.sub(r"[^a-z0-9]", "", ascii_slug)
    return sanitized

# -> Suggests slug candidates based on a company name
# Normalizes and cleans each word using `sanitize_tenant_slug`, ignoring invalid ones
# If 1 word: returns the single cleaned version
# If 2+ words: returns combinations like full join, short join, and full triple
# Removes duplicates and the forbidden term "slug"
# Ex: "Blue Data Labs" → ["bluedata", "bluedat", "bluedatalabs"]
def suggest_company_slug(name: str) -> list[str]:
    if not name:
        return []

    words = name.split()
    clean_words = [sanitize_tenant_slug(w) for w in words if sanitize_tenant_slug(w)]

    if not clean_words:
        return []

    suggestions = []

    if len(clean_words) == 1:
        suggestions.append(clean_words[0])
    else:
        w1, w2 = clean_words[0], clean_words[1]
        full_combo = "".join(clean_words[:3])
        short_combo = w1[:4] + w2[:4]
        two_combo = w1 + w2

        suggestions.extend([
            two_combo,
            short_combo,
            full_combo
        ])

    final = [s for s in dict.fromkeys(suggestions) if s and s != "slug"]

    return final

if __name__ == "__main__":
    company_names = [
        "WORKIZA HVAC & CLEANING",
        "ACME GLOBAL SOLUTIONS",
        "BLUE DATA TECH",
        "SKYLINE LOGISTICS",
        "OMNI ENERGY SYSTEMS",
        "NOVA FINANCIAL GROUP",
        "ATLAS SECURITY SERVICES",
        "PHOENIX LABS INC",
        "QUANTUM HEALTHCARE",
        "TITAN SOFTWARE",
        "ECLIPSE CREATIVE AGENCY",
        "DELTA NETWORK SOLUTIONS",
        "VORTEX INDUSTRIAL SUPPLY",
        "MATRIX AI TECHNOLOGIES",
        "ZENITH CLOUD SERVICES"
    ]

    for name in company_names:
        suggestions = suggest_company_slug(name)
        print(f"\nSlug generated for: {name}")
        if suggestions:
            for s in suggestions:
                print(f"- {s}")
        else:
            print("- [no valid suggestion]")
