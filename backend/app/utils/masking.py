"""Data masking utilities for PII protection."""

import re


def mask_phone(phone: str | None) -> str | None:
    """Mask phone number to prevent direct contact before contract completion.

    Handles common Korean phone number formats and masks the middle digits.

    Args:
        phone: Raw phone number string in any format.

    Returns:
        Masked phone number (e.g., '010-****-5678') or None if input is None/empty.

    Examples:
        >>> mask_phone('01012345678')
        '010-****-5678'
        >>> mask_phone('010-1234-5678')
        '010-****-5678'
        >>> mask_phone('010 1234 5678')
        '010-****-5678'
        >>> mask_phone('0212345678')
        '02-****-5678'
        >>> mask_phone(None)
        None
    """
    if not phone:
        return phone

    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 11:  # Korean mobile: 01012345678
        return f"{digits[:3]}-****-{digits[7:]}"
    elif len(digits) == 10:  # Landline: 0212345678
        return f"{digits[:2]}-****-{digits[6:]}"

    # Fallback: mask middle portion
    if len(digits) > 4:
        return digits[:3] + "****" + digits[-4:]
    return phone
