from copy import deepcopy

import pytest

from eve_wormhole.models import WormholeRecord
from eve_wormhole.state import BookmarkState


@pytest.fixture
def complete(sample):
    state = BookmarkState()
    assert state.paste(sample)
    assert state.paste("Wormhole K162")
    assert state.paste("YRU-123")
    state.set_manual("space_type", "C2")
    state.set_manual("destination", "533")
    assert state.bookmark == "-YRU C2iL 533 EOL"
    return state


def test_complementary_pastes_and_manual_fields(complete):
    complete.set_manual("home", True)
    assert complete.bookmark == "--YRU C2iL 533 EOL"


def test_k162_direction_can_be_overridden(complete):
    complete.set_manual("direction", "s")
    assert complete.bookmark == "-YRU C2sL 533 EOL"
    complete.paste("K162")
    assert complete.bookmark is None
    assert "direction" in complete.conflicts
    complete.keep_manual_values()
    assert complete.bookmark == "-YRU C2sL 533 EOL"


@pytest.mark.parametrize(
    "source", ["ABC-123", "YRU-456", "ABC-123\nDestination: Thera"]
)
def test_new_signature_rejected_atomically(complete, source):
    before = deepcopy(complete.record)
    assert not complete.paste(source)
    assert complete.record == before
    assert "New hole" in complete.message


def test_prefix_can_be_completed():
    state = BookmarkState()
    state.set_manual("signature", "yru")
    assert state.paste("YRU-123")
    assert state.record.signature == "YRU-123"


def test_unknown_paste_does_not_change_record(complete):
    before = deepcopy(complete.record)
    assert not complete.paste("unrelated clipboard contents")
    assert complete.record == before


def test_description_replaces_stale_flags(complete, sample):
    critical = sample.replace("More than 50%", "Less than 10%").replace(
        "4 hours", "1 hour"
    )
    complete.paste(critical)
    assert complete.bookmark == "-YRU C2iL 533 VEOL CRIT"
    complete.paste(sample.replace("Less than 4 hours", "More than 4 hours"))
    assert complete.bookmark == "-YRU C2iL 533"


def test_partial_description_clears_old_parsed_values(complete):
    complete.paste("Destination: Class 1-3 wormhole systems")
    assert complete.record.size == ""
    assert complete.record.lifetime is None
    assert complete.record.mass is None
    assert complete.bookmark is None


def test_manual_class_is_preserved_if_in_new_range(complete, sample):
    assert complete.paste(sample)
    assert complete.bookmark == "-YRU C2iL 533 EOL"


def test_conflict_requires_a_choice(complete, sample):
    complete.set_manual("size", "M")
    complete.paste(sample.replace("Class 1-3", "Class 4-5"))
    assert set(complete.conflicts) == {"space_type", "size"}
    assert complete.bookmark is None
    complete.set_manual("space_type", "C4")
    complete.set_manual("size", "L")
    assert complete.bookmark == "-YRU C4iL 533 EOL"


def test_unknown_status_never_means_healthy(complete, sample):
    complete.paste(sample.replace("More than 50% remaining", "Unknown status"))
    assert "mass" in complete.issues
    assert complete.bookmark is None
    complete.set_manual("mass", "DSTB")
    assert complete.bookmark == "-YRU C2iL 533 EOL DSTB"


def test_reset_clears_record_and_overrides(complete):
    complete.set_manual("home", True)
    complete.reset()
    assert complete.record == WormholeRecord()
    assert not complete.manual_fields
    assert not complete.conflicts
    assert not complete.candidates
    assert complete.bookmark is None
