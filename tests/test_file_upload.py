"""Tests for profile photo upload (Task 4)."""
import pytest
from httpx import AsyncClient
from io import BytesIO


async def _signup_and_get_token(client: AsyncClient, email: str) -> str:
    """Helper: signup and return token."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "testpass123",
            "role": "instructor",
            "display_name": "Photo Test",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _create_test_image(width: int = 100, height: int = 100) -> bytes:
    """Create a minimal valid JPEG image for testing."""
    try:
        from PIL import Image
        img = Image.new("RGB", (width, height), color="red")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except ImportError:
        # Minimal JPEG header for when Pillow is not installed
        return (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
            b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
            b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342'
            b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
            b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
            b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00T\xdb\x9e\xa7K'
            b'\xff\xd9'
        )


@pytest.mark.asyncio
async def test_upload_profile_photo(client: AsyncClient):
    """Upload a profile photo should succeed."""
    token = await _signup_and_get_token(client, "photo_up@test.com")

    image_data = _create_test_image()
    files = {"file": ("test.jpg", BytesIO(image_data), "image/jpeg")}

    response = await client.post(
        "/api/v1/profile/photo",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert response.status_code == 200
    data = response.json()
    assert "urls" in data
    assert "original" in data["urls"]


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient):
    """Upload non-image file should fail."""
    token = await _signup_and_get_token(client, "photo_bad@test.com")

    files = {"file": ("test.txt", BytesIO(b"not an image"), "text/plain")}

    response = await client.post(
        "/api/v1/profile/photo",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UPLOAD_ERROR"


@pytest.mark.asyncio
async def test_delete_photo_no_photo(client: AsyncClient):
    """Delete photo when no photo exists should return 404."""
    token = await _signup_and_get_token(client, "photo_del@test.com")

    response = await client.delete(
        "/api/v1/profile/photo",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_file_upload_service_validation():
    """Test FileUploadService validation logic."""
    from app.services.file_upload import FileUploadService
    from unittest.mock import MagicMock

    service = FileUploadService()

    # Test invalid content type
    mock_file = MagicMock()
    mock_file.content_type = "application/pdf"
    mock_file.filename = "test.pdf"

    with pytest.raises(ValueError, match="지원하지 않는 파일 형식"):
        service._validate_image(mock_file)

    # Test valid content type
    mock_file.content_type = "image/jpeg"
    mock_file.filename = "test.jpg"
    service._validate_image(mock_file)  # Should not raise
