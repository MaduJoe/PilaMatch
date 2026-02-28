"""Email service with mock/SMTP support."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email sending service. Supports mock/smtp/sendgrid backends."""

    async def send_password_reset(self, email: str, token: str) -> None:
        """Send password reset email with reset link."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        subject = "[PilaMatch] 비밀번호 재설정"
        body = (
            f"안녕하세요,\n\n"
            f"비밀번호 재설정을 요청하셨습니다.\n"
            f"아래 링크를 클릭하여 새 비밀번호를 설정해주세요:\n\n"
            f"{reset_url}\n\n"
            f"이 링크는 {settings.PASSWORD_RESET_EXPIRE_MINUTES}분 동안 유효합니다.\n"
            f"비밀번호 재설정을 요청하지 않으셨다면 이 이메일을 무시해주세요.\n\n"
            f"감사합니다,\nPilaMatch 팀"
        )
        await self._send(email, subject, body)

    async def send_account_deletion_notice(self, email: str) -> None:
        """Send account deletion confirmation email."""
        subject = "[PilaMatch] 계정 삭제 예약 안내"
        body = (
            f"안녕하세요,\n\n"
            f"계정 삭제가 예약되었습니다.\n"
            f"30일 이내에 로그인하시면 삭제를 취소할 수 있습니다.\n\n"
            f"감사합니다,\nPilaMatch 팀"
        )
        await self._send(email, subject, body)

    async def _send(self, to: str, subject: str, body: str) -> None:
        """Route to the configured email backend."""
        provider = settings.EMAIL_PROVIDER.lower()
        if provider == "smtp":
            await self._send_smtp(to, subject, body)
        else:
            await self._send_mock(to, subject, body)

    async def _send_mock(self, to: str, subject: str, body: str) -> None:
        """Mock email: log to console (development mode)."""
        logger.info(
            f"[MOCK EMAIL] To: {to} | Subject: {subject}\n"
            f"--- Body ---\n{body}\n--- End ---"
        )

    async def _send_smtp(self, to: str, subject: str, body: str) -> None:
        """Send email via SMTP."""
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info(f"Email sent to {to}: {subject}")
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            raise ValueError(f"이메일 발송에 실패했습니다: {e}")
