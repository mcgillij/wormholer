from dataclasses import replace

import pytest

from eve_wormhole.formatter import format_bookmark
from eve_wormhole.models import DIRECTIONS, SIZES, SPACE_TYPES, WormholeRecord

COMPLETE = WormholeRecord(
    signature="YRU-123",
    space_type="C2",
    direction="i",
    size="L",
    destination="533",
    lifetime="EOL",
    mass="",
)


@pytest.mark.parametrize(
    ("home", "lifetime", "mass", "expected"),
    [
        (False, "EOL", "", "-YRU C2iL 533 EOL"),
        (True, "EOL", "", "--YRU C2iL 533 EOL"),
        (False, "VEOL", "CRIT", "-YRU C2iL 533 VEOL CRIT"),
        (False, "EOL", "DSTB", "-YRU C2iL 533 EOL DSTB"),
        (False, "", "", "-YRU C2iL 533"),
    ],
)
def test_bookmark_examples(home, lifetime, mass, expected):
    assert (
        format_bookmark(replace(COMPLETE, home=home, lifetime=lifetime, mass=mass))
        == expected
    )


@pytest.mark.parametrize("space_type", SPACE_TYPES)
def test_space_type_codes(space_type):
    assert (
        format_bookmark(replace(COMPLETE, space_type=space_type))
        == f"-YRU {space_type}iL 533 EOL"
    )


@pytest.mark.parametrize("direction", DIRECTIONS)
@pytest.mark.parametrize("size", SIZES)
def test_direction_and_size_codes(direction, size):
    assert (
        format_bookmark(replace(COMPLETE, direction=direction, size=size))
        == f"-YRU C2{direction}{size} 533 EOL"
    )


def test_destination_whitespace_preserves_name():
    result = format_bookmark(replace(COMPLETE, destination="  New\n  Caldari\t "))
    assert result == "-YRU C2iL New Caldari EOL"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("signature", "K162"),
        ("signature", "ABC-12"),
        ("space_type", "C1-3"),
        ("direction", "x"),
        ("size", "Large"),
        ("destination", "\t"),
        ("destination", "533\x00"),
        ("lifetime", None),
        ("lifetime", "EOL VEOL"),
        ("mass", None),
        ("mass", "DSTB CRIT"),
        ("wormhole_type", "ABC-123"),
    ],
)
def test_invalid_records_cannot_be_formatted(field, value):
    with pytest.raises(ValueError):
        format_bookmark(replace(COMPLETE, **{field: value}))
