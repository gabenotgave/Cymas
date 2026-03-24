"""Metrics router: CSV-backed endpoints for Cymas monitoring data."""
import csv
import os
from typing import Any

import pandas as pd
from fastapi import APIRouter, Query
from fastapi import HTTPException

from probes import config
from data_io.writer import FIELDNAMES

router = APIRouter()

# Columns used for summary stats (mean, min, max)
SUMMARY_COLS = [
    "http_ttfb_ms",
    "ping_gateway_avg_ms",
    "ping_external_avg_ms",
    "dns_resolution_ms",
    "wifi_snr_db",
    "device_count",
]

# Columns returned by /timeseries (only those present in the dataframe are included)
TIMESERIES_COLS = [
    "timestamp",
    "http_ttfb_ms",
    "ping_gateway_avg_ms",
    "ping_external_avg_ms",
    "dns_resolution_ms",
    "device_count",
    "wifi_snr_db",
    "wifi_tx_rate_mbps",
]


def load_csv() -> pd.DataFrame:
    """Read config CSV, parse timestamps, sort ascending, replace NaN with None-friendly representation."""
    df = pd.read_csv(config.CSV_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp", ascending=True)
    df = df.where(pd.notna(df), None)
    return df


def _serialize_timestamps(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ensure all timestamp values in records are ISO 8601 strings."""
    out: list[dict[str, Any]] = []
    for row in records:
        new_row = dict(row)
        if "timestamp" in new_row and new_row["timestamp"] is not None:
            ts = new_row["timestamp"]
            if hasattr(ts, "isoformat"):
                new_row["timestamp"] = ts.isoformat()
        out.append(new_row)
    return out


def _reset_csv_file() -> None:
    tmp_path = f"{config.CSV_PATH}.tmp"
    os.makedirs(os.path.dirname(config.CSV_PATH), exist_ok=True)
    with open(tmp_path, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
    os.replace(tmp_path, config.CSV_PATH)


@router.get("/raw")
def get_raw(
    limit: int = Query(default=20, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    start: str | None = Query(
        default=None,
        description="Inclusive start datetime (ISO 8601 or 'YYYY-MM-DDTHH:MM' from datetime-local).",
    ),
    end: str | None = Query(
        default=None,
        description="Inclusive end datetime (ISO 8601 or 'YYYY-MM-DDTHH:MM' from datetime-local).",
    ),
) -> dict[str, Any]:
    """Return a paginated slice of raw metrics. Response includes `data` (list of records) and `total` (total count)."""
    try:
        df = load_csv()
        # For the raw table, show most recent samples first
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp", ascending=False)
        if start is not None and start.strip() != "":
            start_dt = pd.to_datetime(start.strip(), errors="coerce")
            if pd.isna(start_dt):
                raise ValueError("Invalid start datetime")
            df = df.loc[df["timestamp"] >= start_dt]
        if end is not None and end.strip() != "":
            end_dt = pd.to_datetime(end.strip(), errors="coerce")
            if pd.isna(end_dt):
                raise ValueError("Invalid end datetime")
            df = df.loc[df["timestamp"] <= end_dt]
        total = len(df)
        slice_df = df.iloc[offset : offset + limit]
        records = slice_df.to_dict(orient="records")
        records = _serialize_timestamps(records)
        return {"data": records, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load or serialize raw metrics: {e!s}")


@router.post("/reset")
def reset_metrics_csv() -> dict[str, Any]:
    """Erase all samples by truncating the CSV back to only the header row."""
    try:
        _reset_csv_file()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics CSV: {e!s}")


@router.get("/summary")
def get_summary() -> dict[str, Any]:
    """Return aggregate stats (mean, min, max) for key numeric columns plus total_samples, first_seen, last_seen."""
    try:
        df = load_csv()
        total_samples = len(df)
        first_ts = df["timestamp"].iloc[0] if total_samples > 0 else None
        last_ts = df["timestamp"].iloc[-1] if total_samples > 0 else None
        first_seen = first_ts.isoformat() if first_ts is not None and hasattr(first_ts, "isoformat") else None
        last_seen = last_ts.isoformat() if last_ts is not None and hasattr(last_ts, "isoformat") else None

        result: dict[str, Any] = {
            "total_samples": total_samples,
            "first_seen": first_seen,
            "last_seen": last_seen,
        }

        for col in SUMMARY_COLS:
            if col not in df.columns:
                continue
            agg = df[col].agg(["mean", "min", "max"])
            result[col] = {
                "mean": agg["mean"] if pd.notna(agg["mean"]) else None,
                "min": agg["min"] if pd.notna(agg["min"]) else None,
                "max": agg["max"] if pd.notna(agg["max"]) else None,
            }

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute summary: {e!s}")


@router.get("/latest")
def get_latest() -> dict[str, Any]:
    """Return the most recent row from the metrics CSV as a single record."""
    try:
        df = load_csv()
        if len(df) == 0:
            raise HTTPException(status_code=500, detail="No data in CSV")
        row = df.iloc[-1].to_dict()
        if "timestamp" in row and row["timestamp"] is not None and hasattr(row["timestamp"], "isoformat"):
            row["timestamp"] = row["timestamp"].isoformat()
        return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load latest metrics: {e!s}")


@router.get("/timeseries")
def get_timeseries() -> list[dict[str, Any]]:
    """Return a reduced timeseries: timestamp plus selected numeric columns; only columns present in the dataframe are included."""
    try:
        df = load_csv()
        available = [c for c in TIMESERIES_COLS if c in df.columns]
        sub = df[available].copy()
        records = sub.to_dict(orient="records")
        records = _serialize_timestamps(records)
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load timeseries: {e!s}")
