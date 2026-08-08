import re

MASS_UNITS_TO_GRAMS = {"kg": 1000, "g": 1, "mg": 0.001, "lb": 453.592, "lbs": 453.592, "oz": 28.3495}
VOLUME_UNITS_TO_ML = {"l": 1000, "ml": 1}

MULTIPACK_RE = re.compile(
    r"(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(kg|mg|g|ml|l|lbs|lb|oz)\b", re.IGNORECASE
)
SINGLE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(kg|mg|g|ml|l|lbs|lb|oz)\b", re.IGNORECASE
)


def extract_quantity(name):
    multipack_matches = list(MULTIPACK_RE.finditer(name))
    if multipack_matches:
        count, value, unit = multipack_matches[-1].groups()
        value = float(count) * float(value)
    else:
        single_matches = list(SINGLE_RE.finditer(name))
        if not single_matches:
            return None
        value, unit = single_matches[-1].groups()
        value = float(value)

    unit = unit.lower()
    if unit in MASS_UNITS_TO_GRAMS:
        return value * MASS_UNITS_TO_GRAMS[unit], "mass"
    return value * VOLUME_UNITS_TO_ML[unit], "volume"


def quantity_compatible(q1, q2, tolerance=0.05):
    if q1 is None or q2 is None:
        return True
    value1, dim1 = q1
    value2, dim2 = q2
    if dim1 != dim2:
        return False
    return abs(value1 - value2) / max(value1, value2) <= tolerance
