from datetime import datetime
import time
import logging
import pandas as pd
import schedule

logger = logging.getLogger(__name__)


def is_reminder_due(
    due_dt: pd.Timestamp,
    frequency: str,
    now: datetime,
    send_all: bool = False,
) -> bool:
    """
    Determines whether a reminder is due at `now`.
    - send_all=True: treats all valid reminders as due (great for demos/testing).
    - once: due if due_dt <= now.
    - daily: due if current HH:MM matches due_dt HH:MM and now >= due_dt.
    - weekly: due if weekday and HH:MM match due_dt and now >= due_dt.
    """
    if pd.isna(due_dt):
        return False

    if send_all:
        return True

    freq = (frequency or "once").strip().lower()
    due_py = due_dt.to_pydatetime()

    if freq == "once":
        return due_py <= now
    if freq == "daily":
        return now >= due_py and (now.hour, now.minute) == (due_py.hour, due_py.minute)
    if freq == "weekly":
        return (
            now >= due_py
            and now.weekday() == due_py.weekday()
            and (now.hour, now.minute) == (due_py.hour, due_py.minute)
        )

    logger.warning("Unknown frequency '%s'; defaulting to 'once' check", freq)
    return due_py <= now


def run_loop(job_fn, interval_seconds: int) -> None:
    """Runs `job_fn` every `interval_seconds` until interrupted with Ctrl+C."""
    logger.info("Starting scheduler loop every %d second(s). Press Ctrl+C to stop.", interval_seconds)
    job_fn()
    schedule.every(interval_seconds).seconds.do(job_fn)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped cleanly by user.")