"""Run Qt tests offscreen so they cannot touch the desktop clipboard."""

import os
from pathlib import Path

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture
def sample() -> str:
    return (Path(__file__).parent / "fixtures" / "k162.txt").read_text()


@pytest.fixture(
    params=[
        (0, ("C1", "C2", "C3"), "L", ""),
        (1, ("C1", "C2", "C3"), "M", "EOL"),
        (2, ("C1", "C2", "C3"), "M", ""),
        (3, ("C1", "C2", "C3"), "M", ""),
        (4, ("HS",), "M", ""),
        (5, ("HS",), "L", ""),
        (6, ("HS",), "L", "EOL"),
        (7, ("C4", "C5"), "L", "EOL"),
        (8, ("NS",), "L", ""),
    ],
    ids=[f"entry-{number}" for number in range(1, 10)],
)
def description_variant(request):
    source = (
        Path(__file__).parent / "fixtures" / "description_variants.txt"
    ).read_text()
    entries = [
        "An unstable wormhole," + entry
        for entry in source.split("An unstable wormhole,")[1:]
    ]
    assert len(entries) == 9
    index, candidates, size, lifetime = request.param
    return entries[index].strip(), candidates, size, lifetime
