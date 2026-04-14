from datetime import time

from src.setup_flows import deadline_from_usual, defaults, varies_defaults


def test_medium_is_recommended_shift():
    assert deadline_from_usual(time(1, 30), "medium") == time(0, 30)


def test_all_difficulties_distinct():
    light = deadline_from_usual(time(2, 0), "light")
    medium = deadline_from_usual(time(2, 0), "medium")
    hard = deadline_from_usual(time(2, 0), "hard")
    assert light == time(1, 30)
    assert medium == time(1, 0)
    assert hard == time(0, 0)


def test_varies_returns_same_as_defaults():
    assert varies_defaults() == defaults()
