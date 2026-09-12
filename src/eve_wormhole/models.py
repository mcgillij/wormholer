"""Bookmark data shared by the parser, formatter, and UI."""

from dataclasses import dataclass, field

SPACE_TYPES = (
    "HS",
    "LS",
    "NS",
    "C1",
    "C2",
    "C3",
    "C4",
    "C5",
    "C6",
    "C13",
    "DR",
    "PV",
    "Thera",
)
DIRECTIONS = {"i": "Incoming", "o": "Outgoing / unsure", "r": "Random", "s": "Static"}
SIZES = {"S": "Small", "M": "Medium", "L": "Large", "XL": "Extra large"}
LIFETIMES = {
    "": "No lifetime flag",
    "EOL": "EOL · less than 4 hours",
    "VEOL": "VEOL · less than 1 hour",
}
MASSES = {
    "": "No mass flag",
    "DSTB": "DSTB · less than 50%",
    "CRIT": "CRIT · less than 10%",
}


@dataclass
class WormholeRecord:
    signature: str = ""
    wormhole_type: str = ""
    space_type: str = ""
    direction: str = "o"
    size: str = ""
    destination: str = ""
    lifetime: str | None = None
    mass: str | None = None
    home: bool = False


@dataclass
class ParseResult:
    values: dict[str, str | None] = field(default_factory=dict)
    candidates: tuple[str, ...] = ()
    issues: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    is_description: bool = False

    @property
    def recognized(self) -> bool:
        return bool(self.values or self.is_description)
