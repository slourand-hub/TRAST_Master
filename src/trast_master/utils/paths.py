import os
import re
from typing import Optional


PULSEWIDTH_PATTERNS = [
    re.compile(r"pw[_\-\s]?(\d+(?:\.\d+)?)\s*(ns|us|ms|s)", re.IGNORECASE),
    re.compile(r"pulse[_\-\s]?width[_\-\s]?(\d+(?:\.\d+)?)\s*(ns|us|ms|s)", re.IGNORECASE),
    re.compile(r"(\d+(?:\.\d+)?)\s*(ns|us|ms|s)", re.IGNORECASE),
]

UNIT_SCALE = {
    "ns": 1e-9,
    "us": 1e-6,
    "ms": 1e-3,
    "s": 1.0,
}


def parse_pulsewidth_seconds_from_name(name: str) -> Optional[float]:
    if not name:
        return None

    base = os.path.basename(str(name))

    for pattern in PULSEWIDTH_PATTERNS:
        match = pattern.search(base)
        if match:
            value = float(match.group(1))
            unit = match.group(2).lower()
            return value * UNIT_SCALE[unit]

    return None


def parse_pulsewidth_from_filename(filename: str) -> tuple[Optional[float], Optional[float]]:
    pw_s = parse_pulsewidth_seconds_from_name(filename)
    if pw_s is None:
        return None, None
    return pw_s, pw_s * 1e9