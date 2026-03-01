"""Recurring schedule utilities for contracts.

Provides helper functions to generate recurring session dates,
find the next upcoming session, and format weekday labels in Korean.
"""

from datetime import date, timedelta
from typing import Optional


def generate_recurring_dates(
    start_date: date,
    end_date: date,
    recurring_days: list[int],
) -> list[date]:
    """Generate list of dates for a recurring schedule.

    Args:
        start_date: First possible date.
        end_date: Last possible date (inclusive).
        recurring_days: List of ISO weekday numbers (1=Monday ... 7=Sunday).

    Returns:
        Sorted list of dates matching the recurring pattern.
    """
    if not recurring_days:
        return []

    recurring_set = set(recurring_days)
    dates: list[date] = []
    current = start_date
    while current <= end_date:
        if current.isoweekday() in recurring_set:
            dates.append(current)
        current += timedelta(days=1)
    return dates


def get_next_session_date(
    today: date,
    recurring_days: list[int],
    end_date: date,
) -> Optional[date]:
    """Get the next upcoming session date from today.

    Searches up to 7 days ahead (one full week) to find the next
    occurrence that falls on one of the recurring weekdays.

    Args:
        today: The reference date to search from (inclusive).
        recurring_days: List of ISO weekday numbers (1=Monday ... 7=Sunday).
        end_date: The last valid date for the recurring schedule.

    Returns:
        The next session date, or None if no session is found within range.
    """
    if not recurring_days:
        return None

    recurring_set = set(recurring_days)
    current = today
    for _ in range(8):  # At most 7 days to find next occurrence
        if current > end_date:
            return None
        if current.isoweekday() in recurring_set:
            return current
        current += timedelta(days=1)
    return None


WEEKDAY_LABELS_KO: dict[int, str] = {
    1: "월",
    2: "화",
    3: "수",
    4: "목",
    5: "금",
    6: "토",
    7: "일",
}


def format_recurring_days_ko(recurring_days: list[int]) -> str:
    """Format recurring days as Korean text.

    Args:
        recurring_days: List of ISO weekday numbers (1=Monday ... 7=Sunday).

    Returns:
        Slash-separated Korean weekday labels. e.g., [1,3,5] -> '월/수/금'.
    """
    sorted_days = sorted(recurring_days)
    return "/".join(WEEKDAY_LABELS_KO.get(d, "?") for d in sorted_days)
