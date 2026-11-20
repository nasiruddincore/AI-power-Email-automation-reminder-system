from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass
class Settings:
    dry_run: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    sender_name: str
    sender_email: str
    poll_interval_seconds: int
    contacts_csv: Path
    reminders_csv: Path
    template_file: Path
    log_file: Path
    output_dir: Path


def get_settings() -> Settings:
    dry_run_raw = os.getenv("DRY_RUN", "true").strip().lower()
    dry_run = dry_run_raw in {"1", "true", "yes", "on"}

    port_raw = os.getenv("SMTP_PORT", "587").strip()
    try:
        smtp_port = int(port_raw)
    except ValueError:
        smtp_port = 587

    interval_raw = os.getenv("POLL_INTERVAL_SECONDS", "30").strip()
    try:
        poll_interval = max(5, int(interval_raw))
    except ValueError:
        poll_interval = 30

    smtp_user = os.getenv("SMTP_USER", "").strip()
    sender_email = os.getenv("SENDER_EMAIL", "").strip() or smtp_user

    return Settings(
        dry_run=dry_run,
        smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com").strip(),
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_pass=os.getenv("SMTP_PASS", "").strip(),
        sender_name=os.getenv("SENDER_NAME", "Reminder Bot").strip(),
        sender_email=sender_email,
        poll_interval_seconds=poll_interval,
        contacts_csv=BASE_DIR / "data" / "contacts.csv",
        reminders_csv=BASE_DIR / "data" / "reminders.csv",
        template_file=BASE_DIR / "templates" / "reminder_template.txt",
        log_file=BASE_DIR / "logs" / "automation.log",
        output_dir=BASE_DIR / "outputs",
    )