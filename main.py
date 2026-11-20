from datetime import datetime
from pathlib import Path
import argparse
import logging
import sys

from src.config import get_settings, Settings
from src.loader import load_contacts, load_reminders, load_template
from src.personalizer import render_message
from src.scheduler import is_reminder_due, run_loop
from src.mailer import send_email
from src.reporter import save_report


def setup_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def process_batch(settings: Settings, send_all: bool = False, force_dry_run: bool | None = None) -> Path | None:
    logger = logging.getLogger(__name__)
    dry_run = settings.dry_run if force_dry_run is None else force_dry_run

    try:
        contacts_df = load_contacts(settings.contacts_csv)
        reminders_df = load_reminders(settings.reminders_csv)
        subject_tmpl, body_tmpl = load_template(settings.template_file)
    except Exception as exc:
        logger.error("Failed to load project inputs: %s", exc)
        return None

    contacts_map = contacts_df.set_index("contact_id").to_dict(orient="index")
    now = datetime.now()
    records: list[dict] = []

    for _, rem in reminders_df.iterrows():
        rem_id = rem["reminder_id"]
        contact_id = rem["contact_id"]
        due_dt = rem["due_dt"]
        freq = rem["frequency"]

        if not is_reminder_due(due_dt, freq, now, send_all=send_all):
            logger.debug("Skipping reminder %s (not due yet)", rem_id)
            continue

        contact = contacts_map.get(contact_id)
        if not contact:
            err_msg = f"Unknown contact_id '{contact_id}'"
            logger.error("[FAILED] Reminder %s -> %s", rem_id, err_msg)
            records.append(
                {
                    "timestamp": now.isoformat(timespec="seconds"),
                    "reminder_id": rem_id,
                    "contact_id": contact_id,
                    "recipient_name": "",
                    "recipient_email": "",
                    "subject": rem["reminder_title"],
                    "status": "FAILED",
                    "detail": err_msg,
                }
            )
            continue

        context = {
            "name": contact.get("name", ""),
            "email": contact.get("email", ""),
            "role": contact.get("role", ""),
            "reminder_title": rem.get("reminder_title", ""),
            "due_at": rem.get("due_at", ""),
            "frequency": freq,
            "notes": rem.get("notes", ""),
            "sender_name": settings.sender_name,
        }

        subject, body, missing_keys = render_message(subject_tmpl, body_tmpl, context)
        if missing_keys:
            logger.warning("Reminder %s has unmapped template keys: %s", rem_id, missing_keys)

        status, detail = send_email(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_pass=settings.smtp_pass,
            sender_name=settings.sender_name,
            sender_email=settings.sender_email,
            recipient_email=contact.get("email", ""),
            subject=subject,
            body=body,
            dry_run=dry_run,
        )

        records.append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "reminder_id": rem_id,
                "contact_id": contact_id,
                "recipient_name": contact.get("name", ""),
                "recipient_email": contact.get("email", ""),
                "subject": subject,
                "status": status,
                "detail": detail,
            }
        )

    if not records:
        logger.info("No reminders due at %s.", now.strftime("%Y-%m-%d %H:%M:%S"))
        return None

    report_path = save_report(records, settings.output_dir)
    sent_count = sum(1 for r in records if r["status"] == "SENT")
    dry_count = sum(1 for r in records if r["status"] == "DRY_RUN")
    fail_count = sum(1 for r in records if r["status"] == "FAILED")
    logger.info(
        "Batch complete -> Total: %d | SENT: %d | DRY_RUN: %d | FAILED: %d",
        len(records),
        sent_count,
        dry_count,
        fail_count,
    )
    return report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Email Automation & Reminder System")
    parser.add_argument(
        "--now",
        action="store_true",
        help="Process all reminders immediately regardless of due_at timestamp.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously on the configured poll interval.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run mode (no real SMTP emails sent).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Force live SMTP mode (overrides DRY_RUN=true in .env).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    setup_logging(settings.log_file)

    force_dry: bool | None = None
    if args.dry_run:
        force_dry = True
    elif args.live:
        force_dry = False

    def job() -> None:
        process_batch(settings, send_all=args.now, force_dry_run=force_dry)

    if args.loop:
        run_loop(job, settings.poll_interval_seconds)
    else:
        job()


if __name__ == "__main__":
    main()