"""Validate and format bookmarks without importing Qt."""

import re

from eve_wormhole.models import (
    DIRECTIONS,
    LIFETIMES,
    MASSES,
    SIZES,
    SPACE_TYPES,
    WormholeRecord,
)


def clean_text(value: str) -> str:
    return " ".join(value.split())


def validation_errors(record: WormholeRecord) -> dict[str, str]:
    errors = {}
    if not re.fullmatch(r"[A-Z]{3}(?:-\d{3})?", record.signature):
        errors["signature"] = "Enter a signature, such as YRU-123 or YRU."
    if record.wormhole_type and not re.fullmatch(r"[A-Z]\d{3}", record.wormhole_type):
        errors["wormhole_type"] = (
            "Enter a wormhole type such as K162, or leave it empty."
        )
    if record.space_type not in SPACE_TYPES:
        errors["space_type"] = "Choose the exact destination class."
    if record.direction not in DIRECTIONS:
        errors["direction"] = "Choose a direction."
    if record.size not in SIZES:
        errors["size"] = "Choose the maximum ship size."
    if not clean_text(record.destination):
        errors["destination"] = "Enter a destination name or label."
    elif any(ord(char) < 32 and not char.isspace() for char in record.destination):
        errors["destination"] = "Remove control characters from the destination."
    if record.lifetime not in LIFETIMES:
        errors["lifetime"] = "Set the lifetime status."
    if record.mass not in MASSES:
        errors["mass"] = "Set the mass status."
    return errors


def format_bookmark(record: WormholeRecord) -> str:
    if errors := validation_errors(record):
        raise ValueError(" ".join(errors.values()))
    prefix = "--" if record.home else "-"
    parts = [
        f"{prefix}{record.signature[:3]}",
        f"{record.space_type}{record.direction}{record.size}",
        clean_text(record.destination),
    ]
    parts.extend(flag for flag in (record.lifetime, record.mass) if flag)
    return " ".join(parts)
