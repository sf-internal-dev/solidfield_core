from typing import Set

# --- Types catalog (keep aligned with the current FIELD_TYPE) ---
NUMERIC_TYPES: Set[str] = {
    "number", "degree",
    # Metric
    "length_cm", "width_cm", "height_cm", "area_m2", "volume_l", "weight_kg",
    # Imperial
    "length_in", "width_in", "height_in", "area_ft2", "volume_gal", "weight_lb",
    # Electric 
    "voltage", "current_amp", "frequency_hz", "power_w", "power_kw",
    # Environmental
    "temperature", "temperature_f", "pressure", "humidity_pct",
    "speed_kmh", "speed_mph",
}
