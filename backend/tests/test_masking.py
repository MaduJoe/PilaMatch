"""Unit tests for data masking utilities."""

import pytest

from app.utils.masking import mask_phone


class TestMaskPhone:
    """Tests for mask_phone function."""

    # --- Happy path: standard Korean mobile formats ---

    def test_mask_11_digit_no_separator(self) -> None:
        """Standard 11-digit mobile without separators."""
        assert mask_phone("01012345678") == "010-****-5678"

    def test_mask_hyphen_separated(self) -> None:
        """Standard hyphen-separated format."""
        assert mask_phone("010-1234-5678") == "010-****-5678"

    def test_mask_space_separated(self) -> None:
        """Space-separated format."""
        assert mask_phone("010 1234 5678") == "010-****-5678"

    def test_mask_dot_separated(self) -> None:
        """Dot-separated format (uncommon but valid)."""
        assert mask_phone("010.1234.5678") == "010-****-5678"

    def test_mask_mixed_separators(self) -> None:
        """Mixed separator format."""
        assert mask_phone("010-1234 5678") == "010-****-5678"

    # --- Landline (10-digit) ---

    def test_mask_10_digit_landline(self) -> None:
        """10-digit Seoul landline."""
        assert mask_phone("0212345678") == "02-****-5678"

    def test_mask_10_digit_landline_with_hyphens(self) -> None:
        """10-digit landline with hyphens."""
        assert mask_phone("02-1234-5678") == "02-****-5678"

    # --- Preserves last 4 digits ---

    def test_last_four_digits_preserved(self) -> None:
        """The last four digits of the original number should always be visible."""
        result = mask_phone("010-9876-5432")
        assert result is not None
        assert result.endswith("5432")

    def test_middle_digits_hidden(self) -> None:
        """The middle digits must be replaced with ****."""
        result = mask_phone("010-1234-5678")
        assert result is not None
        assert "****" in result
        assert "1234" not in result

    # --- Edge cases: None and empty ---

    def test_none_input(self) -> None:
        """None input returns None."""
        assert mask_phone(None) is None

    def test_empty_string(self) -> None:
        """Empty string returns empty string (falsy)."""
        assert mask_phone("") == ""

    # --- Fallback for unusual lengths ---

    def test_short_number_under_5_digits(self) -> None:
        """Numbers with 4 or fewer digits are returned as-is."""
        assert mask_phone("1234") == "1234"

    def test_fallback_for_other_lengths(self) -> None:
        """Numbers that are not 10 or 11 digits use fallback masking."""
        result = mask_phone("0311234567890")  # 13 digits
        assert result is not None
        assert "****" in result
        # Fallback: first 3 + **** + last 4
        assert result == "031****7890"

    # --- Different mobile prefixes ---

    def test_mask_011_prefix(self) -> None:
        """Old 011 mobile prefix (11 digits)."""
        assert mask_phone("01112345678") == "011-****-5678"

    def test_mask_016_prefix(self) -> None:
        """Old 016 mobile prefix (11 digits)."""
        assert mask_phone("01612345678") == "016-****-5678"
