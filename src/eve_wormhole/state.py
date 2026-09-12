"""Merge complementary pastes without carrying data into another wormhole."""

from dataclasses import fields

from eve_wormhole.formatter import clean_text, format_bookmark, validation_errors
from eve_wormhole.models import ParseResult, WormholeRecord
from eve_wormhole.parser import parse_paste

FIELD_NAMES = {field.name for field in fields(WormholeRecord)}


class BookmarkState:
    def __init__(self) -> None:
        self.record = WormholeRecord()
        self.manual_fields: set[str] = set()
        self.candidates: tuple[str, ...] = ()
        self.issues: dict[str, str] = {}
        self.conflicts: dict[str, str] = {}
        self.message = ""

    def reset(self) -> None:
        self.__init__()

    @property
    def errors(self) -> dict[str, str]:
        errors = validation_errors(self.record)
        if self.candidates and not self.record.space_type:
            errors["space_type"] = f"Choose {' / '.join(self.candidates)}."
        errors.update(self.issues)
        errors.update(self.conflicts)
        return errors

    @property
    def bookmark(self) -> str | None:
        return None if self.errors else format_bookmark(self.record)

    def set_manual(self, field: str, value: str | bool | None) -> None:
        if field not in FIELD_NAMES:
            raise ValueError(f"Unknown field: {field}")
        if isinstance(value, str):
            value = clean_text(value)
            if field in ("signature", "wormhole_type"):
                value = value.upper()
        setattr(self.record, field, value)
        self.manual_fields.add(field)
        self.issues.pop(field, None)
        self.conflicts.pop(field, None)
        self.message = ""
        if field == "wormhole_type":
            self._update_direction()

    def _update_direction(self) -> None:
        direction = "i" if self.record.wormhole_type == "K162" else "o"
        if "direction" not in self.manual_fields:
            self.record.direction = direction
        elif direction == "i" and self.record.direction != "i":
            self.conflicts["direction"] = (
                "K162 indicates incoming. Review your direction or keep your values."
            )
        else:
            self.conflicts.pop("direction", None)

    def keep_manual_values(self) -> None:
        """An explicit user action acknowledges conflicts with their chosen values."""
        for field in self.manual_fields:
            self.conflicts.pop(field, None)
            self.issues.pop(field, None)

    def paste(self, text: str) -> bool:
        return self.apply(parse_paste(text))

    def apply(self, result: ParseResult) -> bool:
        self.message = ""
        if result.errors:
            self.message = " ".join(result.errors)
            return False
        if not result.recognized:
            self.message = "No wormhole information found. Paste a description, ABC-123 signature, type, or J-number."
            return False
        incoming_signature = result.values.get("signature")
        current = self.record.signature
        # A manually entered three-letter prefix may be completed by its full ID.
        if (
            incoming_signature
            and current
            and incoming_signature != current
            and (len(current) != 3 or incoming_signature[:3] != current)
        ):
            self.message = "Different signature. Use New hole before pasting it."
            return False

        if result.is_description:
            self.candidates = result.candidates
            for field in ("space_type", "size", "lifetime", "mass"):
                self.issues.pop(field, None)
                self.conflicts.pop(field, None)

        for field, value in result.values.items():
            current = getattr(self.record, field)
            if field == "signature":
                self.record.signature = value
                self.issues.pop(field, None)
                continue
            if field not in self.manual_fields:
                setattr(self.record, field, value)
                continue
            if field == "space_type" and self.candidates:
                disagrees = current not in self.candidates
            else:
                # Missing evidence does not erase a deliberate manual choice.
                supplied = value is not None and (
                    value != "" or field in ("lifetime", "mass")
                )
                disagrees = supplied and current != value
            if disagrees:
                shown = (
                    " / ".join(self.candidates)
                    if field == "space_type"
                    else (value or "no flag")
                )
                self.conflicts[field] = (
                    f"Pasted {field.replace('_', ' ')} is {shown}. Review your choice or keep your values."
                )
            else:
                self.conflicts.pop(field, None)

        self.issues.update(result.issues)
        if "wormhole_type" in result.values:
            self._update_direction()
        return True
