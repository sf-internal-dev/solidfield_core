import re
from typing import Tuple, List, Optional, Dict, Any, Iterable

def _is_boolish(v: Any) -> bool:
    if isinstance(v, bool):
        return True
    if isinstance(v, str) and v.strip().lower() in ("true", "false", "1", "0"):
        return True
    return False

def _is_positive_int(v: Any) -> bool:
    if isinstance(v, int) and v > 0:
        return True
    if isinstance(v, str) and v.isdigit() and int(v) > 0:
        return True
    return False

def _only_printable_no_ctrl(s: str) -> bool:
    # blocks control characters (keeps normal whitespace)
    return not re.search(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", s)

def _split_choice_options(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    parts: List[str] = []
    for chunk in str(raw).replace(",", "\n").splitlines():
        v = chunk.strip()
        if v and v not in parts:
            parts.append(v)
    return parts
