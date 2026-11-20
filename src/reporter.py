from datetime import datetime
from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def save_report(records: list[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"delivery_report_{timestamp}.csv"

    columns = [
        "timestamp",
        "reminder_id",
        "contact_id",
        "recipient_name",
        "recipient_email",
        "subject",
        "status",
        "detail",
    ]
    df = pd.DataFrame(records, columns=columns)
    df.to_csv(report_path, index=False, encoding="utf-8")
    logger.info("Saved delivery report with %d row(s) to %s", len(df), report_path)
    return report_path