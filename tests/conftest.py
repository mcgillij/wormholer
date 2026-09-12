"""Run Qt tests offscreen so they cannot touch the desktop clipboard."""

import os
from pathlib import Path

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture
def sample() -> str:
    return (Path(__file__).parent / "fixtures" / "k162.txt").read_text()
