"""Tests for file upload magic bytes validation.

The FileUploadService._validate_magic_bytes() method checks the first bytes
of uploaded file data against known image file signatures (JPEG, PNG, WebP).
This prevents Content-Type spoofing attacks where malicious files are
uploaded with image extensions or content-types.
"""

import pytest
from app.services.file_upload import FileUploadService


class TestMagicBytesValidation:
    """Tests for _validate_magic_bytes file signature checking."""

    def setup_method(self):
        self.service = FileUploadService()

    def test_magic_bytes_valid_jpeg(self):
        """Valid JPEG file passes magic bytes check."""
        # JPEG magic bytes: FF D8 FF
        jpeg_data = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        self.service._validate_magic_bytes(jpeg_data)  # Should not raise

    def test_magic_bytes_valid_jpeg_exif(self):
        """JPEG with EXIF header passes magic bytes check."""
        # JPEG with EXIF: FF D8 FF E1
        jpeg_exif_data = b"\xff\xd8\xff\xe1" + b"\x00" * 100
        self.service._validate_magic_bytes(jpeg_exif_data)  # Should not raise

    def test_magic_bytes_valid_png(self):
        """Valid PNG file passes magic bytes check."""
        # PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        self.service._validate_magic_bytes(png_data)  # Should not raise

    def test_magic_bytes_valid_webp(self):
        """Valid WebP file passes magic bytes check."""
        # WebP: RIFF....WEBP
        webp_data = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 100
        self.service._validate_magic_bytes(webp_data)  # Should not raise

    def test_magic_bytes_rejects_text_file(self):
        """Text file disguised as image is rejected."""
        text_data = b"This is not an image file at all" + b"\x00" * 100
        with pytest.raises(ValueError, match="이미지 형식"):
            self.service._validate_magic_bytes(text_data)

    def test_magic_bytes_rejects_html(self):
        """HTML file disguised as image is rejected (XSS vector)."""
        html_data = (
            b'<html><script>alert("xss")</script></html>' + b"\x00" * 100
        )
        with pytest.raises(ValueError, match="이미지 형식"):
            self.service._validate_magic_bytes(html_data)

    def test_magic_bytes_rejects_too_small(self):
        """File smaller than 12 bytes is rejected."""
        with pytest.raises(ValueError, match="너무 작습니다"):
            self.service._validate_magic_bytes(b"\xff\xd8")

    def test_magic_bytes_rejects_empty(self):
        """Empty file is rejected."""
        with pytest.raises(ValueError, match="너무 작습니다"):
            self.service._validate_magic_bytes(b"")

    def test_magic_bytes_rejects_pdf(self):
        """PDF file disguised as image is rejected."""
        pdf_data = b"%PDF-1.4 " + b"\x00" * 100
        with pytest.raises(ValueError, match="이미지 형식"):
            self.service._validate_magic_bytes(pdf_data)

    def test_magic_bytes_rejects_exe(self):
        """Windows executable disguised as image is rejected."""
        exe_data = b"MZ" + b"\x00" * 110
        with pytest.raises(ValueError, match="이미지 형식"):
            self.service._validate_magic_bytes(exe_data)

    def test_magic_bytes_rejects_zip(self):
        """ZIP archive disguised as image is rejected."""
        zip_data = b"PK\x03\x04" + b"\x00" * 108
        with pytest.raises(ValueError, match="이미지 형식"):
            self.service._validate_magic_bytes(zip_data)

    def test_magic_bytes_rejects_elf(self):
        """Linux ELF binary disguised as image is rejected."""
        elf_data = b"\x7fELF" + b"\x00" * 108
        with pytest.raises(ValueError, match="이미지 형식"):
            self.service._validate_magic_bytes(elf_data)

    def test_magic_bytes_boundary_12_bytes_jpeg(self):
        """Exactly 12-byte JPEG passes (minimum valid size)."""
        jpeg_12 = b"\xff\xd8\xff\xe0" + b"\x00" * 8
        self.service._validate_magic_bytes(jpeg_12)  # Should not raise

    def test_magic_bytes_boundary_11_bytes_rejected(self):
        """11-byte file is rejected (below minimum)."""
        with pytest.raises(ValueError, match="너무 작습니다"):
            self.service._validate_magic_bytes(b"\xff\xd8\xff" + b"\x00" * 8)


class TestValidateImage:
    """Tests for _validate_image content-type and extension checking."""

    def setup_method(self):
        self.service = FileUploadService()

    def test_rejects_invalid_content_type(self):
        """Non-image content type is rejected."""
        from unittest.mock import MagicMock

        mock_file = MagicMock()
        mock_file.content_type = "application/pdf"
        mock_file.filename = "test.pdf"

        with pytest.raises(ValueError, match="지원하지 않는 파일 형식"):
            self.service._validate_image(mock_file)

    def test_rejects_invalid_extension(self):
        """Non-image extension is rejected."""
        from unittest.mock import MagicMock

        mock_file = MagicMock()
        mock_file.content_type = "image/jpeg"
        mock_file.filename = "test.gif"

        with pytest.raises(ValueError, match="지원하지 않는 확장자"):
            self.service._validate_image(mock_file)

    def test_accepts_valid_jpeg(self):
        """Valid JPEG file passes both checks."""
        from unittest.mock import MagicMock

        mock_file = MagicMock()
        mock_file.content_type = "image/jpeg"
        mock_file.filename = "photo.jpg"

        self.service._validate_image(mock_file)  # Should not raise

    def test_accepts_valid_png(self):
        """Valid PNG file passes both checks."""
        from unittest.mock import MagicMock

        mock_file = MagicMock()
        mock_file.content_type = "image/png"
        mock_file.filename = "photo.png"

        self.service._validate_image(mock_file)  # Should not raise

    def test_accepts_valid_webp(self):
        """Valid WebP file passes both checks."""
        from unittest.mock import MagicMock

        mock_file = MagicMock()
        mock_file.content_type = "image/webp"
        mock_file.filename = "photo.webp"

        self.service._validate_image(mock_file)  # Should not raise
