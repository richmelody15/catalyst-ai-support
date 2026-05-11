import smtplib
from email.mime.text import MIMEText
import os
import logging

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email via SMTP using env variables.

    Required env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
    Returns True on success, False on failure.
    """
    from config import settings

    smtp_host = os.environ.get("SMTP_HOST", settings.SMTP_HOST)
    smtp_port = int(os.environ.get("SMTP_PORT", settings.SMTP_PORT))
    smtp_user = os.environ.get("SMTP_USER", settings.SMTP_USER)
    smtp_pass = os.environ.get("SMTP_PASS", settings.SMTP_PASS)

    if not all([smtp_user, smtp_pass]):
        logger.warning("SMTP credentials missing — email not sent")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to], msg.as_string())
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return False
