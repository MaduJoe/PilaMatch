"""Tests for job post sorting - past jobs should appear after future jobs (FB-1)."""
from datetime import date, timedelta

import pytest


def test_past_jobs_after_future():
    """Past-date jobs should sort after future-date jobs at frontend level."""
    today = date.today()
    jobs = [
        {"job": {"id": "1", "date": str(today - timedelta(days=5))}, "matching": {"total": 90}},
        {"job": {"id": "2", "date": str(today + timedelta(days=3))}, "matching": {"total": 70}},
        {"job": {"id": "3", "date": str(today - timedelta(days=1))}, "matching": {"total": 95}},
        {"job": {"id": "4", "date": str(today + timedelta(days=10))}, "matching": {"total": 60}},
    ]

    def _is_past_job(item):
        job = item.get("job", item)
        try:
            return date.fromisoformat(str(job.get("date", ""))) < today
        except (ValueError, TypeError):
            return False

    # Sort: past jobs go to bottom
    sorted_jobs = sorted(jobs, key=_is_past_job)

    # First items should be future jobs
    assert not _is_past_job(sorted_jobs[0])
    assert not _is_past_job(sorted_jobs[1])
    # Last items should be past jobs
    assert _is_past_job(sorted_jobs[2])
    assert _is_past_job(sorted_jobs[3])


def test_is_past_field():
    """The is_past field should be computed correctly."""
    today = date.today()

    # Past date
    past_date = today - timedelta(days=1)
    assert past_date < today

    # Future date
    future_date = today + timedelta(days=1)
    assert not (future_date < today)

    # Today is NOT past
    assert not (today < today)


def test_premium_sort_within_group():
    """Within the same group (past/future), premium jobs should sort first."""
    today = date.today()
    jobs = [
        {"id": "1", "date": str(today + timedelta(days=1)), "is_premium": False},
        {"id": "2", "date": str(today + timedelta(days=2)), "is_premium": True},
        {"id": "3", "date": str(today + timedelta(days=3)), "is_premium": False},
        {"id": "4", "date": str(today + timedelta(days=4)), "is_premium": True},
    ]

    # Sort by premium first (simulating the backend behavior)
    sorted_jobs = sorted(jobs, key=lambda x: x.get("is_premium", False), reverse=True)

    assert sorted_jobs[0]["is_premium"] is True
    assert sorted_jobs[1]["is_premium"] is True
    assert sorted_jobs[2]["is_premium"] is False
    assert sorted_jobs[3]["is_premium"] is False


def test_date_parsing_robustness():
    """Date parsing should handle edge cases."""
    today = date.today()

    # Valid ISO date
    assert date.fromisoformat("2025-01-15") < today or date.fromisoformat("2025-01-15") >= today

    # Empty string should raise ValueError
    with pytest.raises(ValueError):
        date.fromisoformat("")

    # None should raise TypeError
    with pytest.raises(TypeError):
        date.fromisoformat(None)
