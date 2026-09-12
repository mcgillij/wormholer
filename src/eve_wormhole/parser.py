"""Parse explicit English EVE information and identifiers into partial records."""

import re
import unicodedata

from eve_wormhole.models import ParseResult

LABELS = {
    "destination": "space_type",
    "maximum ship size": "size",
    "reliable lifetime": "lifetime",
    "mass stability": "mass",
}
SIZE_NAMES = {"small": "S", "medium": "M", "large": "L", "extra large": "XL"}
SPACE_NAMES = {
    "high security": "HS",
    "high security space": "HS",
    "high security systems": "HS",
    "low security": "LS",
    "low security space": "LS",
    "low security systems": "LS",
    "null security": "NS",
    "null security space": "NS",
    "null security systems": "NS",
    "triglavian space": "PV",
    "pochven": "PV",
    "drifter wormhole systems": "DR",
    "drifter space": "DR",
    "thera": "Thera",
    "shattered wormhole systems": "C13",
}


def normalize_source(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(
        str.maketrans({"–": "-", "—": "-"})
    )
    return "\n".join(" ".join(line.split()) for line in text.splitlines()).strip()


def _space_type(value: str) -> tuple[str, ...]:
    value = value.casefold().rstrip(".")
    if match := re.fullmatch(r"class ([1-6])\s*-\s*([1-6]) wormhole systems?", value):
        lower, upper = map(int, match.groups())
        return tuple(f"C{number}" for number in range(lower, upper + 1))
    if match := re.fullmatch(r"class (1[3]|[1-6]) wormhole systems?", value):
        return (f"C{match[1]}",)
    if re.fullmatch(r"c(?:[1-6]|13)", value):
        return (value.upper(),)
    if value in ("hs", "ls", "ns", "dr", "pv"):
        return (value.upper(),)
    if code := SPACE_NAMES.get(value.replace("-", " ")):
        return (code,)
    return ()


def _lifetime(value: str) -> str | None:
    value = value.casefold().rstrip(".")
    if re.fullmatch(r"less than 1 hours? remaining", value):
        return "VEOL"
    if value == "less than 4 hours remaining":
        return "EOL"
    if (match := re.fullmatch(r"more than (\d+) hours? remaining", value)) and int(
        match[1]
    ) >= 4:
        return ""
    if value in (
        "less than 1 day remaining",
        "more than 1 day remaining",
        "more than a day remaining",
    ):
        return ""
    return None


def _mass(value: str) -> str | None:
    return {
        "more than 50% remaining": "",
        "less than 50% remaining": "DSTB",
        "less than 10% remaining": "CRIT",
    }.get(value.casefold().rstrip("."))


def parse_paste(text: str) -> ParseResult:
    result = ParseResult()
    source = normalize_source(text)
    signatures = set(
        re.findall(r"(?<![A-Z0-9-])[A-Z]{3}-\d{3}(?![A-Z0-9-])", source, re.IGNORECASE)
    )
    signatures = {value.upper() for value in signatures}
    if len(signatures) > 1:
        result.errors.append("Paste one scan signature at a time.")
    elif signatures:
        result.values["signature"] = signatures.pop()

    types = set(re.findall(r"\bwormhole ([A-Z]\d{3})\b", source, re.IGNORECASE))
    if re.fullmatch(r"[A-Z]\d{3}", source, re.IGNORECASE):
        types.add(source)
    types = {value.upper() for value in types}
    if len(types) > 1:
        result.errors.append("Paste one wormhole type at a time.")
    elif types:
        result.values["wormhole_type"] = types.pop()

    if re.fullmatch(r"J\d{6}", source, re.IGNORECASE):
        result.values["destination"] = source.upper()

    found = {}
    for line in source.splitlines():
        label, separator, value = line.partition(":")
        key = label.strip().casefold()
        if not separator or key not in LABELS:
            continue
        result.is_description = True
        if key in found:
            result.errors.append(f"More than one {key} line. Paste one description.")
        found[key] = value.strip()

    if not result.is_description:
        return result

    # A new description owns all four status fields, including missing values.
    result.values.update(space_type="", size="", lifetime=None, mass=None)
    for label, value in found.items():
        field = LABELS[label]
        if field == "space_type":
            result.candidates = _space_type(value)
            if len(result.candidates) == 1:
                result.values[field] = result.candidates[0]
            known = bool(result.candidates)
        elif field == "size":
            result.values[field] = SIZE_NAMES.get(value.casefold().rstrip("."), "")
            known = bool(result.values[field])
        else:
            result.values[field] = (
                _lifetime(value) if field == "lifetime" else _mass(value)
            )
            known = result.values[field] is not None
        if not known:
            result.issues[field] = (
                f"Unrecognized {label}: {value or '(empty)'}. Choose a value below."
            )
    return result
