"""Parse axis tick label strings (scientific notation, LaTeX-style)."""

from __future__ import annotations

import math
import re


def parse_tick_label(text: str | None) -> float | None:
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    s = s.replace('−', '-').replace('–', '-').replace('×', 'x').replace('·', '.')
    s = re.sub(r'\s+', '', s)
    s = s.replace('$', '').replace('{', '').replace('}', '').replace('\\', '')

    # 10^n, 10^{n}, 1e-3, 2x10^4
    sci = re.match(
        r'^([+-]?[\d.]+)?\s*(?:x?\s*10\^?\(?(-?\d+)\)?|e([+-]?\d+))$',
        s,
        re.I,
    )
    if sci:
        base = float(sci.group(1) or 1)
        exp = int(sci.group(2) or sci.group(3))
        return base * (10**exp)

    # Plain 10^n without base
    if re.match(r'^10\^?\(?(-?\d+)\)?$', s, re.I):
        exp = int(re.search(r'(-?\d+)', s).group(1))
        return 10.0**exp

    s2 = s.replace(',', '')
    try:
        v = float(s2)
        if math.isfinite(v):
            return v
    except ValueError:
        pass
    return None


def resolve_tick_value(
    raw_value: object | None,
    label_text: str | None = None,
) -> float | None:
    """Prefer parsed label_text when it disagrees with numeric value field."""
    from_val = None
    if raw_value is not None:
        try:
            from_val = float(raw_value)
            if not math.isfinite(from_val):
                from_val = None
        except (TypeError, ValueError):
            from_val = None

    from_label = parse_tick_label(label_text)
    if from_label is not None and from_val is not None:
        if from_val == 0 and from_label != 0:
            return from_label
        if from_val > 0 and from_label > 0:
            ratio = max(from_val, from_label) / min(from_val, from_label)
            if ratio > 5:
                return from_label
        return from_val
    return from_label if from_label is not None else from_val
