import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body_html: str):
    """Send email via SMTP (Phase 5 full implementation)."""
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.SMTP_USER
    message["To"] = to
    message.attach(MIMEText(body_html, "html"))
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"[EMAIL] Sent to {to}: {subject}")
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send to {to}: {e}")
        raise
