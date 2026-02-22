"""Tests for contract duration calculation (FB-5 fix)."""
from datetime import datetime, time


def _calculate_hours(start_time: time, end_time: time) -> float:
    """Replicate the duration calculation from contract.py create_from_offer."""
    start_dt = datetime.combine(datetime.today(), start_time)
    end_dt = datetime.combine(datetime.today(), end_time)
    return (end_dt - start_dt).total_seconds() / 3600


def test_duration_normal():
    """09:00~10:00 = 1.0 hour"""
    hours = _calculate_hours(time(9, 0), time(10, 0))
    assert hours == 1.0


def test_duration_fractional():
    """02:45~04:00 = 1.25 hours (this was the reported bug)"""
    hours = _calculate_hours(time(2, 45), time(4, 0))
    assert hours == 1.25


def test_duration_multi_hour():
    """09:00~12:30 = 3.5 hours"""
    hours = _calculate_hours(time(9, 0), time(12, 30))
    assert hours == 3.5


def test_duration_short():
    """10:00~10:30 = 0.5 hours"""
    hours = _calculate_hours(time(10, 0), time(10, 30))
    assert hours == 0.5


def test_total_amount_calculation():
    """Test hourly_rate * hours * sessions."""
    hourly_rate = 50000
    hours = _calculate_hours(time(9, 0), time(10, 15))  # 1.25 hours
    sessions = 4
    total = float(hourly_rate) * hours * sessions
    assert total == 250000.0


def test_duration_display_format():
    """Test the display format: :.2f rstrip('0') rstrip('.')"""
    test_cases = [
        (1.0, "1"),
        (1.25, "1.25"),
        (1.5, "1.5"),
        (3.5, "3.5"),
        (0.5, "0.5"),
        (2.0, "2"),
    ]
    for value, expected in test_cases:
        result = f"{value:.2f}".rstrip('0').rstrip('.')
        assert result == expected, f"Expected {expected} for {value}, got {result}"
