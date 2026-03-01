"""Tests for recurring schedule service.

Covers date generation, next session lookup, and Korean label formatting.
"""

from datetime import date

import pytest

from app.services.recurring_schedule import (
    generate_recurring_dates,
    get_next_session_date,
    format_recurring_days_ko,
)


# ---------------------------------------------------------------------------
# generate_recurring_dates
# ---------------------------------------------------------------------------


class TestGenerateRecurringDates:
    """Tests for generate_recurring_dates."""

    def test_mon_wed_fri(self) -> None:
        """Monday/Wednesday/Friday over two weeks yields 4-6 dates."""
        # 2026-03-02 is Monday
        start = date(2026, 3, 2)
        end = date(2026, 3, 13)  # Friday
        result = generate_recurring_dates(start, end, [1, 3, 5])
        expected = [
            date(2026, 3, 2),   # Mon
            date(2026, 3, 4),   # Wed
            date(2026, 3, 6),   # Fri
            date(2026, 3, 9),   # Mon
            date(2026, 3, 11),  # Wed
            date(2026, 3, 13),  # Fri
        ]
        assert result == expected

    def test_tue_thu(self) -> None:
        """Tuesday/Thursday pattern."""
        start = date(2026, 3, 3)  # Tue
        end = date(2026, 3, 12)   # Thu
        result = generate_recurring_dates(start, end, [2, 4])
        expected = [
            date(2026, 3, 3),   # Tue
            date(2026, 3, 5),   # Thu
            date(2026, 3, 10),  # Tue
            date(2026, 3, 12),  # Thu
        ]
        assert result == expected

    def test_every_day(self) -> None:
        """All 7 weekdays selected produces every day in range."""
        start = date(2026, 3, 2)
        end = date(2026, 3, 8)
        result = generate_recurring_dates(start, end, [1, 2, 3, 4, 5, 6, 7])
        assert len(result) == 7
        assert result[0] == start
        assert result[-1] == end

    def test_empty_recurring_days(self) -> None:
        """Empty recurring_days list returns empty list."""
        result = generate_recurring_dates(date(2026, 3, 2), date(2026, 3, 8), [])
        assert result == []

    def test_single_day_range(self) -> None:
        """start_date == end_date returns that date if it matches."""
        # 2026-03-02 is Monday (isoweekday=1)
        result = generate_recurring_dates(date(2026, 3, 2), date(2026, 3, 2), [1])
        assert result == [date(2026, 3, 2)]

    def test_single_day_range_no_match(self) -> None:
        """start_date == end_date but weekday doesn't match returns empty."""
        # 2026-03-02 is Monday, looking for Tuesday
        result = generate_recurring_dates(date(2026, 3, 2), date(2026, 3, 2), [2])
        assert result == []

    def test_end_before_start(self) -> None:
        """end_date before start_date returns empty list."""
        result = generate_recurring_dates(date(2026, 3, 10), date(2026, 3, 2), [1, 3, 5])
        assert result == []

    def test_weekend_only(self) -> None:
        """Saturday/Sunday pattern across two weeks."""
        start = date(2026, 3, 1)   # Sunday
        end = date(2026, 3, 15)    # Sunday
        result = generate_recurring_dates(start, end, [6, 7])
        expected = [
            date(2026, 3, 1),   # Sun
            date(2026, 3, 7),   # Sat
            date(2026, 3, 8),   # Sun
            date(2026, 3, 14),  # Sat
            date(2026, 3, 15),  # Sun
        ]
        assert result == expected

    def test_dates_are_sorted(self) -> None:
        """Returned dates are always in chronological order."""
        start = date(2026, 3, 2)
        end = date(2026, 3, 20)
        result = generate_recurring_dates(start, end, [5, 1])  # Fri, Mon (unsorted input)
        for i in range(len(result) - 1):
            assert result[i] < result[i + 1]


# ---------------------------------------------------------------------------
# get_next_session_date
# ---------------------------------------------------------------------------


class TestGetNextSessionDate:
    """Tests for get_next_session_date."""

    def test_today_is_session_day(self) -> None:
        """If today is a recurring day, return today."""
        # 2026-03-02 is Monday
        today = date(2026, 3, 2)
        end = date(2026, 3, 31)
        result = get_next_session_date(today, [1, 3, 5], end)
        assert result == date(2026, 3, 2)

    def test_tomorrow_is_session_day(self) -> None:
        """If today is not a recurring day, return the next matching day."""
        # 2026-03-03 is Tuesday, next Mon/Wed/Fri session is Wed 3/4
        today = date(2026, 3, 3)
        end = date(2026, 3, 31)
        result = get_next_session_date(today, [1, 3, 5], end)
        assert result == date(2026, 3, 4)

    def test_end_date_exceeded(self) -> None:
        """Return None if end_date is before next possible session."""
        # 2026-03-03 is Tuesday, next Mon is 3/9, but end is 3/4
        today = date(2026, 3, 3)
        end = date(2026, 3, 4)
        result = get_next_session_date(today, [1], end)  # Monday only
        assert result is None

    def test_returns_none_when_no_match(self) -> None:
        """Return None when today is past end_date."""
        today = date(2026, 4, 1)
        end = date(2026, 3, 31)
        result = get_next_session_date(today, [1, 3, 5], end)
        assert result is None

    def test_empty_recurring_days(self) -> None:
        """Empty recurring days returns None."""
        result = get_next_session_date(date(2026, 3, 2), [], date(2026, 3, 31))
        assert result is None

    def test_wraps_around_week(self) -> None:
        """Find next session that wraps to the following week."""
        # 2026-03-06 is Friday, Sunday-only schedule
        today = date(2026, 3, 6)
        end = date(2026, 3, 31)
        result = get_next_session_date(today, [7], end)  # Sunday only
        assert result == date(2026, 3, 8)  # Next Sunday


# ---------------------------------------------------------------------------
# format_recurring_days_ko
# ---------------------------------------------------------------------------


class TestFormatRecurringDaysKo:
    """Tests for format_recurring_days_ko."""

    def test_mon_wed_fri(self) -> None:
        """[1, 3, 5] formats to '월/수/금'."""
        assert format_recurring_days_ko([1, 3, 5]) == "월/수/금"

    def test_tue_thu(self) -> None:
        """[2, 4] formats to '화/목'."""
        assert format_recurring_days_ko([2, 4]) == "화/목"

    def test_all_days(self) -> None:
        """All 7 days formatted correctly."""
        assert format_recurring_days_ko([1, 2, 3, 4, 5, 6, 7]) == "월/화/수/목/금/토/일"

    def test_single_day(self) -> None:
        """Single day returns just that label."""
        assert format_recurring_days_ko([6]) == "토"

    def test_unsorted_input(self) -> None:
        """Unsorted input is sorted before formatting."""
        assert format_recurring_days_ko([5, 1, 3]) == "월/수/금"

    def test_empty_list(self) -> None:
        """Empty list returns empty string."""
        assert format_recurring_days_ko([]) == ""

    def test_weekend(self) -> None:
        """Weekend days."""
        assert format_recurring_days_ko([6, 7]) == "토/일"

    def test_invalid_day_number(self) -> None:
        """Invalid day number uses '?' placeholder."""
        assert format_recurring_days_ko([8]) == "?"
        assert format_recurring_days_ko([0, 1]) == "?/월"
