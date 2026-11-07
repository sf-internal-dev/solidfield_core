from typing import Callable, Dict, Any
import re

class NumberCodec:
    def __init__(self, canon_unit: str | None, parse: Callable[[Any], float], fmt: Callable[[float], str]):
        self.canon_unit = canon_unit
        self.parse = parse
        self.fmt = fmt

def _to_float(x) -> float:
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        s = x.strip().replace(",", ".")  # accepts a pt-BR decimal comma
        return float(s)
    raise ValueError("not a number")

def _fmt_default(x: float, unit: str | None, digits=2) -> str:
    s = f"{x:.{digits}f}".rstrip("0").rstrip(".")
    return f"{s}{(' ' + unit) if unit else ''}"

# --- Specific parsers ---
_feet_in_pat = re.compile(r"^\s*(\d+)\s*(?:ft|')\s*(\d+)?\s*(?:in|\"|″)?\s*$", re.I)

def parse_height_imperial(val: Any) -> float:
    # Returns canonical **centimeters**
    if isinstance(val, (int, float)):  # already in centimeters?
        return float(val)
    if isinstance(val, str):
        s = val.strip().lower().replace("’", "'").replace("′", "'")
        m = _feet_in_pat.match(s)
        if m:
            feet = int(m.group(1))
            inches = int(m.group(2) or 0)
            total_in = feet * 12 + inches
            return total_in * 2.54  # cm
        # fallback: plain number -> cm
        return _to_float(s)
    raise ValueError("invalid height imperial")

def fmt_height_cm(x_cm: float) -> str:
    # Displays as 1,75 m (pt-BR)
    meters = x_cm / 100.0
    s = f"{meters:.2f}".replace(".", ",")
    return f"{s} m"

def parse_percent_0_100(val: Any) -> float:
    # Canonical: 0..100
    if isinstance(val, str) and "%" in val:
        return _to_float(val.replace("%", ""))
    return _to_float(val)

def fmt_percent(x: float) -> str:
    return f"{x:.0f}%"

# --- Numeric registry ---
NUMERIC_CODECS: Dict[str, NumberCodec] = {
    # General
    "number": NumberCodec(None, parse=_to_float, fmt=lambda x: _fmt_default(x, None)),
    "degree": NumberCodec("°", parse=_to_float, fmt=lambda x: _fmt_default(x, "°", 1)),

    # Metric
    "length_cm": NumberCodec("cm", parse=_to_float, fmt=lambda x: _fmt_default(x, "cm")),
    "height_cm": NumberCodec("cm", parse=_to_float, fmt=lambda x: _fmt_default(x, "cm")),
    "area_m2": NumberCodec("m²", parse=_to_float, fmt=lambda x: _fmt_default(x, "m²")),
    "volume_l": NumberCodec("L", parse=_to_float, fmt=lambda x: _fmt_default(x, "L")),
    "weight_kg": NumberCodec("kg", parse=_to_float, fmt=lambda x: _fmt_default(x, "kg")),

    # Imperial
    "length_in": NumberCodec("in", parse=_to_float, fmt=lambda x: _fmt_default(x, "in")),
    "height_in": NumberCodec("cm", parse=parse_height_imperial, fmt=fmt_height_cm),  # stores **cm**

    # Electrical
    "voltage": NumberCodec("V", parse=_to_float, fmt=lambda x: _fmt_default(x, "V")),
    "current_amp": NumberCodec("A", parse=_to_float, fmt=lambda x: _fmt_default(x, "A")),
    "frequency_hz": NumberCodec("Hz", parse=_to_float, fmt=lambda x: _fmt_default(x, "Hz")),
    "power_w": NumberCodec("W", parse=_to_float, fmt=lambda x: _fmt_default(x, "W")),
    "power_kw": NumberCodec("kW", parse=_to_float, fmt=lambda x: _fmt_default(x, "kW")),

    # Environmental
    "temperature": NumberCodec("°C", parse=_to_float, fmt=lambda x: _fmt_default(x, "°C", 1)),
    "temperature_f": NumberCodec("°C",  # canonical **°C**
        parse=lambda v: ( _to_float(v) - 32.0 ) * 5.0/9.0,
        fmt=lambda x_c: _fmt_default(x_c, "°C", 1)
    ),
    "humidity_pct": NumberCodec("%", parse=parse_percent_0_100, fmt=fmt_percent),
    "speed_kmh": NumberCodec("km/h", parse=_to_float, fmt=lambda x: _fmt_default(x, "km/h")),
    "speed_mph": NumberCodec("km/h",  # canonical km/h
        parse=lambda v: _to_float(v) * 1.60934,
        fmt=lambda x: _fmt_default(x, "km/h")
    ),
    # Pressure — pick one canonical unit: here “psi”
    "pressure": NumberCodec("psi",
        parse=lambda v: _to_float(v),  # could accept “bar” by detecting the suffix and converting
        fmt=lambda x: _fmt_default(x, "psi", 2)
    ),
}
