from datetime import time

from src.setup_flows import deadline_from_usual, defaults, validate_tightening


def test_tighten_accepts_earlier():
    assert validate_tightening(time(23, 30), time(23, 0)) is True


def test_tighten_rejects_equal():
    assert validate_tightening(time(23, 30), time(23, 30)) is False


def test_tighten_rejects_later():
    assert validate_tightening(time(23, 30), time(23, 45)) is False


def test_guided_light_shift():
    assert deadline_from_usual(time(0, 30), "light") == time(0, 0)


def test_guided_medium_shift():
    assert deadline_from_usual(time(1, 0), "medium") == time(0, 0)


def test_guided_hard_shift():
    assert deadline_from_usual(time(2, 0), "hard") == time(0, 0)


def test_guided_shift_wraps_midnight():
    assert deadline_from_usual(time(0, 30), "medium") == time(23, 30)


def test_defaults_are_midnight_ish():
    bed, wake = defaults()
    assert bed == time(23, 30)
    assert wake == time(7, 30)
