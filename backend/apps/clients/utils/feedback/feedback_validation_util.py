import re
from collections import Counter
from backend.i18n.keywords import STOPWORDS_EN, GENERIC_KEYWORDS_EN, GENERIC_KEYWORDS_DE

def stars_given(stars: int, max_stars: int = 5):
    labels = {
        1: "Bad",
        2: "Poor",
        3: "Average",
        4: "Good",
        5: "Excellent"
    }
    stars = max(1, min(stars, max_stars))

    return stars, labels.get(stars, "Unknown")

def reached_comment_max_characters(comment: str, max_lenght: int = 150) -> bool:
    return True if len(comment) >= max_lenght else False

def feedback_preview(comment: str, length: int = 50) -> str:
    comment = comment.strip()
    return comment if len(comment) <= length else comment[:length] + "..."

def is_positive_feedback(stars: int) -> bool:
    return stars >= 4


def _extract_keywords(comment: str, stopwords: set, top_n: int = 10):
    comment = comment or ""
    words = re.findall(r"\b\w+\b", comment.lower())
    filtered = [w for w in words if w not in stopwords and len(w) > 2]
    return Counter(filtered).most_common(top_n)

def extract_keywords_en(feedback_qs, top_n: int = 10):
    all_text = " ".join(f.comment or "" for f in feedback_qs)
    return _extract_keywords(all_text, STOPWORDS_EN, top_n)

def get_generic_keywords(lang="en"):
    return GENERIC_KEYWORDS_EN if lang == "en" else GENERIC_KEYWORDS_DE
