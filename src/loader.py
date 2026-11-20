from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_CONTACT_COLS = {"contact_id", "name", "email"}
REQUIRED_REMINDER_COLS = {"reminder_id", "contact_id", "reminder_title", "due_at"}


def load_contacts(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Contacts CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    df.columns = [col.strip() for col in df.columns]

    missing = REQUIRED_CONTACT_COLS - set(df.columns)
    if missing:
        raise ValueError(f"contacts.csv missing required columns: {sorted(missing)}")

    for col in df.columns:
        df[col] = df[col].str.strip()

    df = df[df["contact_id"] != ""].drop_duplicates(subset=["contact_id"], keep="first")
    logger.info("Loaded %d valid contacts from %s", len(df), csv_path.name)
    return df


def load_reminders(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Reminders CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    df.columns = [col.strip() for col in df.columns]

    missing = REQUIRED_REMINDER_COLS - set(df.columns)
    if missing:
        raise ValueError(f"reminders.csv missing required columns: {sorted(missing)}")

    for col in df.columns:
        df[col] = df[col].str.strip()

    if "frequency" not in df.columns:
        df["frequency"] = "once"
    else:
        df["frequency"] = df["frequency"].replace("", "once").str.lower()

    if "notes" not in df.columns:
        df["notes"] = ""

    df["due_dt"] = pd.to_datetime(df["due_at"], errors="coerce")
    bad_dates = df["due_dt"].isna().sum()
    if bad_dates > 0:
        logger.warning("Found %d reminder(s) with unparseable due_at timestamps", bad_dates)

    logger.info("Loaded %d reminders from %s", len(df), csv_path.name)
    return df


def load_template(template_path: Path) -> tuple[str, str]:
    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    raw_text = template_path.read_text(encoding="utf-8")
    lines = raw_text.splitlines()

    if not lines or not lines[0].lower().startswith("subject:"):
        raise ValueError("Template must start with a 'Subject: ...' line.")

    subject_tmpl = lines[0].split(":", 1)[1].strip()
    body_tmpl = "\n".join(lines[1:]).lstrip("\r\n")
    return subject_tmpl, body_tmpl