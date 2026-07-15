from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
import json

from app.admin.services import export_timestamp, fetch_export_records


EXPORT_COLUMNS = (
    "exported_at",
    "user_id",
    "account_type",
    "email",
    "phone",
    "full_name",
    "age",
    "state",
    "district",
    "occupation",
    "custom_occupation",
    "location_type",
    "preferred_language",
    "gender",
    "income_range",
    "disability_status",
    "marital_status",
    "social_category",
    "profile_completed",
    "created_at",
    "last_login_at",
    "updated_at",
)


@dataclass(frozen=True)
class ExportPayload:
    content: bytes
    media_type: str
    filename: str
    exported_at: str
    record_count: int


def build_export(file_format: str) -> ExportPayload:
    if file_format not in {"csv", "json"}:
        raise ValueError("Unsupported export format.")
    timestamp = export_timestamp()
    records = [
        {"exported_at": timestamp, **{key: row.get(key) for key in EXPORT_COLUMNS[1:]}}
        for row in fetch_export_records()
    ]
    filename_timestamp = timestamp.replace("-", "").replace(":", "").replace("+00:00", "Z")
    if file_format == "csv":
        content = _csv_bytes(records)
        media_type = "text/csv; charset=utf-8"
    else:
        content = json.dumps(
            {
                "exported_at": timestamp,
                "record_count": len(records),
                "records": records,
            },
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
        media_type = "application/json; charset=utf-8"
    return ExportPayload(
        content=content,
        media_type=media_type,
        filename=f"user_export_{filename_timestamp}.{file_format}",
        exported_at=timestamp,
        record_count=len(records),
    )


def _csv_bytes(records: list[dict]) -> bytes:
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        writer.writerow({key: _safe_csv_value(record.get(key)) for key in EXPORT_COLUMNS})
    # UTF-8 with a BOM remains valid UTF-8 and opens Indian scripts correctly in Excel.
    return output.getvalue().encode("utf-8-sig")


def _safe_csv_value(value) -> str | int:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return value
    text = str(value)
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text
