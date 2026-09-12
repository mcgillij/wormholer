import pytest

from eve_wormhole.parser import parse_paste


def test_sample_preserves_missing_information(sample):
    result = parse_paste(sample)
    assert result.values == {
        "space_type": "",
        "size": "L",
        "lifetime": "EOL",
        "mass": "",
    }
    assert result.candidates == ("C1", "C2", "C3")
    assert not result.issues
    assert not result.errors


@pytest.mark.parametrize(
    ("source", "field", "value"),
    [
        ("Wormhole K162", "wormhole_type", "K162"),
        ("k162", "wormhole_type", "K162"),
        ("Wormhole N110", "wormhole_type", "N110"),
        ("YRU-123\tCosmic Signature\tWormhole\t100.0%", "signature", "YRU-123"),
        ("yru-123", "signature", "YRU-123"),
        ("j123456", "destination", "J123456"),
    ],
)
def test_identifiers(source, field, value):
    assert parse_paste(source).values == {field: value}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("High Security", ("HS",)),
        ("Low-Security space", ("LS",)),
        ("Null Security", ("NS",)),
        ("Class 1 wormhole systems", ("C1",)),
        ("Class 2 wormhole systems", ("C2",)),
        ("Class 3 wormhole systems", ("C3",)),
        ("Class 4 wormhole systems", ("C4",)),
        ("Class 5 wormhole systems", ("C5",)),
        ("Class 6 wormhole systems", ("C6",)),
        ("Class 13 wormhole systems", ("C13",)),
        ("Class 1–3 wormhole systems", ("C1", "C2", "C3")),
        ("Class 4-5 wormhole systems", ("C4", "C5")),
        ("Shattered wormhole systems", ("C13",)),
        ("Drifter Wormhole Systems", ("DR",)),
        ("Triglavian Space", ("PV",)),
        ("Thera", ("Thera",)),
    ],
)
def test_destination_classes(text, expected):
    assert parse_paste(f"Destination: {text}").candidates == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Small", "S"),
        ("Medium", "M"),
        ("Large", "L"),
        ("Extra Large", "XL"),
    ],
)
def test_ship_size(text, expected):
    assert parse_paste(f"Maximum Ship Size: {text}").values["size"] == expected


@pytest.mark.parametrize(
    ("label", "text", "field", "expected"),
    [
        ("Reliable Lifetime", "Less than 1 hour remaining", "lifetime", "VEOL"),
        ("Reliable Lifetime", "Less than 4 hours remaining", "lifetime", "EOL"),
        ("Reliable Lifetime", "More than 4 hours remaining", "lifetime", ""),
        ("Reliable Lifetime", "More than 24 hours remaining", "lifetime", ""),
        ("Mass Stability", "More than 50% remaining", "mass", ""),
        ("Mass Stability", "Less than 50% remaining", "mass", "DSTB"),
        ("Mass Stability", "Less than 10% remaining", "mass", "CRIT"),
    ],
)
def test_statuses(label, text, field, expected):
    assert parse_paste(f"{label}: {text}").values[field] == expected


@pytest.mark.parametrize(
    "source",
    [
        "YRU-123 ABC-456",
        "Wormhole K162\nWormhole N110",
        "Destination: Thera\nDestination: High Security",
    ],
)
def test_rejects_multiple_records(source):
    assert parse_paste(source).errors


@pytest.mark.parametrize(
    ("source", "field"),
    [
        ("Destination: Class 1-3-ish", "space_type"),
        ("Destination: Class 3-1 wormhole systems", "space_type"),
        ("Maximum Ship Size: Very Large", "size"),
        ("Reliable Lifetime: Less than 24 hours remaining", "lifetime"),
        ("Reliable Lifetime: More than 1 hour remaining", "lifetime"),
        ("Mass Stability: Less than 90% remaining", "mass"),
        ("Mass Stability:", "mass"),
    ],
)
def test_unknown_values_need_manual_resolution(source, field):
    assert field in parse_paste(source).issues


def test_whitespace_and_case(sample):
    dirty = sample.lower().replace(" ", "\u00a0").replace("\n", "\r\n")
    assert parse_paste(dirty) == parse_paste(sample)


@pytest.mark.parametrize(
    "source", ["", "some unrelated text", "ABC-12", "XABC-123", "-YRU C2iL 533 EOL"]
)
def test_unrelated_or_formatted_text_is_not_input(source):
    assert not parse_paste(source).recognized
