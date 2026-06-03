import re


def parse_number(text: str) -> float | None:
    text = text.strip().replace(",", "").replace("−", "-").replace(" ", "")
    m = re.match(r"^(-?\d+\.?\d*)[×x*]10\^?(-?\d+)$", text)
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2))
    m = re.match(r"^-?\d+\.?\d*(?:[eE][-+]?\d+)?$", text)
    return float(m.group()) if m else None


def extract_unit(text: str) -> str | None:
    m = re.search(r"[\(\[]([^\)\]]+)[\)\]]", text)
    return m.group(1) if m else None
