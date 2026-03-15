"""File upload service with local/S3 storage backends."""

import logging
import os
import uuid
from io import BytesIO
from typing import Optional

from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

CERT_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
CERT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
MAX_SIZE_BYTES = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
LOCAL_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")


class FileUploadService:
    """Local (dev) / S3 (production) file upload service."""

    async def upload_profile_photo(self, user_id: str, file: UploadFile) -> dict:
        """Upload and resize profile photo.

        Returns:
            dict with original, thumbnail (200x200), medium (600x600) URLs.
        """
        self._validate_image(file)
        data = await file.read()
        self._validate_magic_bytes(data)

        if len(data) > MAX_SIZE_BYTES:
            raise ValueError(
                f"파일 크기가 {settings.UPLOAD_MAX_SIZE_MB}MB를 초과합니다"
            )

        ext = self._get_extension(file.filename or "photo.jpg")
        file_id = uuid.uuid4().hex[:16]
        base_path = f"profiles/{user_id}/{file_id}"

        # Resize images
        sizes = await self._resize_image(data, ext)

        # Save all sizes
        urls = {}
        for size_name, img_data in sizes.items():
            key = f"{base_path}_{size_name}{ext}"
            url = await self._save(key, img_data)
            urls[size_name] = url

        logger.info(f"Uploaded profile photo for user {user_id}: {base_path}")
        return urls

    async def upload_certification(self, user_id: str, file: UploadFile) -> dict:
        """Upload certification file (image or PDF).

        Returns:
            dict with file_url and resized image bytes (for Vision API).
        """
        self._validate_cert_file(file)
        data = await file.read()

        if len(data) > MAX_SIZE_BYTES:
            raise ValueError(
                f"파일 크기가 {settings.UPLOAD_MAX_SIZE_MB}MB를 초과합니다"
            )

        ext = self._get_extension(file.filename or "cert.jpg")
        file_id = uuid.uuid4().hex[:16]
        key = f"certs/{user_id}/{file_id}{ext}"

        # Save original
        file_url = await self._save(key, data)

        # For Vision API: resize image to 1568px max (cost optimization)
        vision_image_bytes = None
        if ext != ".pdf":
            self._validate_cert_magic_bytes(data)
            try:
                from PIL import Image

                img = Image.open(BytesIO(data))
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                img.thumbnail((1568, 1568), Image.LANCZOS)
                buf = BytesIO()
                fmt = "JPEG" if ext in (".jpg", ".jpeg") else "PNG"
                img.save(buf, format=fmt, quality=90)
                vision_image_bytes = buf.getvalue()
            except ImportError:
                vision_image_bytes = data

        logger.info(f"Uploaded certification for user {user_id}: {key}")
        return {
            "file_url": file_url,
            "original_filename": file.filename,
            "vision_image_bytes": vision_image_bytes,
            "is_pdf": ext == ".pdf",
        }

    def _validate_cert_file(self, file: UploadFile) -> None:
        """Validate certification file (images + PDF)."""
        if file.content_type and file.content_type not in CERT_CONTENT_TYPES:
            raise ValueError(
                f"지원하지 않는 파일 형식입니다. JPEG, PNG, WebP, PDF만 허용됩니다. "
                f"(received: {file.content_type})"
            )
        if file.filename:
            ext = self._get_extension(file.filename)
            if ext not in CERT_EXTENSIONS:
                raise ValueError(f"지원하지 않는 확장자입니다: {ext}")

    def _validate_cert_magic_bytes(self, data: bytes) -> None:
        """Validate cert image magic bytes (JPEG, PNG, WebP)."""
        if len(data) < 12:
            raise ValueError("파일이 너무 작습니다")
        if data[:3] == b'\xff\xd8\xff':
            return
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return
        if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return
        raise ValueError("파일 내용이 허용된 이미지 형식과 일치하지 않습니다")

    async def delete_profile_photo(self, user_id: str, photo_url: str) -> None:
        """Delete a profile photo and its variants."""
        if settings.STORAGE_BACKEND == "s3":
            await self._delete_s3(photo_url)
        else:
            await self._delete_local(photo_url)

    def _validate_magic_bytes(self, data: bytes) -> None:
        """Validate file content by checking magic bytes (file signature).

        Prevents Content-Type spoofing attacks where malicious files
        are uploaded with image extensions/content-types.

        Args:
            data: Raw file bytes to validate.

        Raises:
            ValueError: If file signature does not match JPEG, PNG, or WebP.
        """
        if len(data) < 12:
            raise ValueError("파일이 너무 작습니다")

        # JPEG: starts with FF D8 FF
        if data[:3] == b'\xff\xd8\xff':
            return

        # PNG: starts with 89 50 4E 47 0D 0A 1A 0A
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return

        # WebP: starts with RIFF....WEBP
        if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return

        raise ValueError(
            "파일 내용이 허용된 이미지 형식(JPEG, PNG, WebP)과 일치하지 않습니다"
        )

    def _validate_image(self, file: UploadFile) -> None:
        """Validate file type and extension."""
        if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"지원하지 않는 파일 형식입니다. JPEG, PNG, WebP만 허용됩니다. "
                f"(received: {file.content_type})"
            )

        if file.filename:
            ext = self._get_extension(file.filename)
            if ext not in ALLOWED_EXTENSIONS:
                raise ValueError(
                    f"지원하지 않는 확장자입니다: {ext}"
                )

    def _get_extension(self, filename: str) -> str:
        """Extract file extension."""
        _, ext = os.path.splitext(filename.lower())
        return ext if ext else ".jpg"

    async def _resize_image(self, data: bytes, ext: str) -> dict[str, bytes]:
        """Resize image to original, thumbnail (200x200), medium (600x600).

        Uses Pillow if available, otherwise returns original only.
        """
        result = {"original": data}

        try:
            from PIL import Image

            img = Image.open(BytesIO(data))

            # Convert RGBA to RGB for JPEG
            if img.mode == "RGBA" and ext in (".jpg", ".jpeg"):
                img = img.convert("RGB")

            fmt = "JPEG" if ext in (".jpg", ".jpeg") else "PNG" if ext == ".png" else "WEBP"

            # Thumbnail (200x200)
            thumb = img.copy()
            thumb.thumbnail((200, 200), Image.LANCZOS)
            buf = BytesIO()
            thumb.save(buf, format=fmt, quality=85)
            result["thumbnail"] = buf.getvalue()

            # Medium (600x600)
            medium = img.copy()
            medium.thumbnail((600, 600), Image.LANCZOS)
            buf = BytesIO()
            medium.save(buf, format=fmt, quality=90)
            result["medium"] = buf.getvalue()

        except ImportError:
            logger.warning("Pillow not installed, skipping image resize")

        return result

    async def _save(self, key: str, data: bytes) -> str:
        """Save file using configured backend."""
        if settings.STORAGE_BACKEND == "s3":
            return await self._save_s3(key, data)
        return await self._save_local(key, data)

    async def _save_local(self, path: str, data: bytes) -> str:
        """Save file to local filesystem."""
        full_path = os.path.join(LOCAL_UPLOAD_DIR, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(data)

        # Return URL path relative to the upload directory
        return f"/uploads/{path}"

    async def _save_s3(self, key: str, data: bytes) -> str:
        """Save file to S3."""
        try:
            import boto3

            s3 = boto3.client("s3", region_name=settings.S3_REGION)
            s3.put_object(
                Bucket=settings.S3_BUCKET,
                Key=key,
                Body=data,
                ContentType="image/jpeg",
            )
            return f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{key}"
        except ImportError:
            logger.error("boto3 not installed, falling back to local storage")
            return await self._save_local(key, data)

    async def _delete_local(self, url: str) -> None:
        """Delete local file."""
        if url.startswith("/uploads/"):
            path = url[len("/uploads/"):]
            full_path = os.path.join(LOCAL_UPLOAD_DIR, path)
            if os.path.exists(full_path):
                os.remove(full_path)

    async def _delete_s3(self, url: str) -> None:
        """Delete S3 file."""
        try:
            import boto3

            # Extract key from URL
            prefix = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/"
            if url.startswith(prefix):
                key = url[len(prefix):]
                s3 = boto3.client("s3", region_name=settings.S3_REGION)
                s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)
        except ImportError:
            logger.error("boto3 not installed")
