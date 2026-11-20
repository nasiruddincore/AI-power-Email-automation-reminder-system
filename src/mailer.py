from email.message import EmailMessage
import logging
import re
import smtplib

logger = logging.getLogger(__name__)
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(address: str) -> bool:
    return bool(address and EMAIL_REGEX.match(address.strip()))


def send_email(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    sender_name: str,
    sender_email: str,
    recipient_email: str,
    subject: str,
    body: str,
    dry_run: bool = True,
    timeout: int = 15,
) -> tuple[str, str]:
    """
    Sends an email via SMTP STARTTLS or simulates sending when dry_run=True.
    Returns (status, detail_message) where status is 'SENT', 'DRY_RUN', or 'FAILED'.
    """
    if not is_valid_email(recipient_email):
        return "FAILED", f"Invalid recipient email: '{recipient_email}'"

    if dry_run:
        logger.info("[DRY-RUN] To: %s | Subject: %s", recipient_email, subject)
        return "DRY_RUN", "Simulated send (DRY_RUN=true)"

    if not smtp_user or not smtp_pass or not is_valid_email(sender_email):
        return "FAILED", "Missing SMTP_USER, SMTP_PASS, or valid SENDER_EMAIL in .env"

    msg = EmailMessage()
    msg["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(host=smtp_host, port=smtp_port, timeout=timeout) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logger.info("[SENT] To: %s | Subject: %s", recipient_email, subject)
        return "SENT", "Delivered via SMTP STARTTLS"
    except smtplib.SMTPAuthenticationError as exc:
        err = f"SMTP authentication failed: {exc}"
        logger.error("[FAILED] %s -> %s", recipient_email, err)
        return "FAILED", err
    except smtplib.SMTPException as exc:
        err = f"SMTP error: {exc}"
        logger.error("[FAILED] %s -> %s", recipient_email, err)
        return "FAILED", err
    except OSError as exc:
        err = f"Network/connection error: {exc}"
        logger.error("[FAILED] %s -> %s", recipient_email, err)
        return "FAILED", err
    except Exception as exc:
        err = f"Unexpected send error: {exc}"
        logger.error("[FAILED] %s -> %s", recipient_email, err)
        return "FAILED", err