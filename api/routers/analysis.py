"""Analysis endpoints for LANtern metrics."""
from __future__ import annotations

import os
from typing import Any

import litellm
import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.routers.metrics import load_csv

load_dotenv()

router = APIRouter()

METRICS = [
        "http_ttfb_ms",
        "ping_gateway_avg_ms",
        "ping_external_avg_ms",
        "dns_resolution_ms",
        "wifi_snr_db",
        "device_count",
        "wifi_tx_rate_mbps",
    ]


class AnalysisRequest(BaseModel):
    start_time: str
    end_time: str


def filter_range(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Filter dataframe to rows between start and end timestamps."""
    if "timestamp" not in df.columns:
        raise HTTPException(status_code=400, detail="No timestamp column found in data")

    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    start_dt = pd.to_datetime(start, errors="coerce")
    end_dt = pd.to_datetime(end, errors="coerce")
    if pd.isna(start_dt) or pd.isna(end_dt):
        raise HTTPException(status_code=400, detail="Invalid start_time or end_time")

    mask = (df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)
    filtered = df.loc[mask].copy()
    if filtered.empty:
        raise HTTPException(status_code=400, detail="No data found for the selected time range")

    filtered = filtered.sort_values("timestamp", ascending=True)
    return filtered


def _round_float(value: Any) -> Any:
    if isinstance(value, (float, int)) and not pd.isna(value):
        return round(float(value), 2)
    return value if value is None or not isinstance(value, float) else value


def compute_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Compute summary statistics for key metrics within the filtered range."""
    

    result: dict[str, Any] = {}

    for col in METRICS:
        if col not in df.columns:
            continue
        agg = df[col].agg(["mean", "min", "max", "std"])
        result[f"{col}_mean"] = _round_float(agg.get("mean"))
        result[f"{col}_min"] = _round_float(agg.get("min"))
        result[f"{col}_max"] = _round_float(agg.get("max"))
        result[f"{col}_std"] = _round_float(agg.get("std"))

    total_samples = len(df)
    result["total_samples"] = int(total_samples)

    first_ts = df["timestamp"].iloc[0]
    last_ts = df["timestamp"].iloc[-1]
    result["start_time"] = first_ts.isoformat() if hasattr(first_ts, "isoformat") else str(first_ts)
    result["end_time"] = last_ts.isoformat() if hasattr(last_ts, "isoformat") else str(last_ts)

    try:
        duration_minutes = (last_ts - first_ts).total_seconds() / 60.0
        result["duration_minutes"] = round(duration_minutes, 1)
    except Exception:
        result["duration_minutes"] = None

    # Most common SSID, if column exists and non-empty
    wifi_ssid = None
    if "wifi_ssid" in df.columns:
        try:
            mode = df["wifi_ssid"].mode(dropna=True)
            if not mode.empty:
                wifi_ssid = mode.iloc[0]
        except Exception:
            wifi_ssid = None
    result["wifi_ssid"] = wifi_ssid

    return result


SYSTEM_PROMPT = """You are a professional network engineer performing a root cause analysis on a home WiFi network using data from a monitoring tool called LANtern.

STATISTICAL SIGNIFICANCE RULES — follow these strictly:
- Only treat an anomaly as meaningful if it occurs in 2+ consecutive samples OR repeats more than 3 times across the selected time range.
- Single isolated spikes must be mentioned briefly under Weak Signals but never elevated to a primary finding.
- Home networks have natural variance of 20-40% in latency metrics. Do not flag variance within this range unless it is sustained.

CORRELATION RULES:
- Prioritize findings where 2 or more metrics degrade simultaneously.
- A spike in one metric with no corresponding change in others is likely noise — say so explicitly.
- Device count correlation is the strongest signal. Weight it heavily.

FORMATTING RULES:
- All timestamps must be written in human readable UTC format: e.g. "Monday March 16, 2026 at 2:45 PM UTC".
- Do not use any HTML, markdown, asterisks, pound signs, backticks, or special characters of any kind. Plain text only.
- Follow the output format below exactly. Every label must appear on its own line. Do not combine labels. Do not skip labels. Do not reorder labels.

OUTPUT FORMAT — copy this structure exactly for every response:

SUMMARY
Write 2-3 sentences here. Overall health assessment only.

FINDINGS
FINDING: One sentence describing what was observed.
METRICS: List the affected metrics.
TIME: Human readable UTC timestamp or range.
CONFIDENCE: High, Medium, or Low.

FINDING: One sentence describing what was observed.
METRICS: List the affected metrics.
TIME: Human readable UTC timestamp or range.
CONFIDENCE: High, Medium, or Low.

WEAK SIGNALS
FINDING: One sentence describing a low confidence observation.
METRICS: List the affected metrics.
TIME: Human readable UTC timestamp or range.
CONFIDENCE: Low.

RECOMMENDATIONS
ACTION: One specific actionable recommendation.
ACTION: One specific actionable recommendation.

If there are no meaningful findings write "None." under FINDINGS. If the network is healthy write "None." under RECOMMENDATIONS. Do not add any extra labels, sections, or commentary outside of this structure."""


Z_SCORE_THRESHOLD = 3


def build_prompt(stats: dict[str, Any], anomalies: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build a LiteLLM-compatible messages list from stats and anomalies."""
    wifi_ssid = stats.get("wifi_ssid") or "unknown"
    start_time = stats.get("start_time") or "unknown"
    end_time = stats.get("end_time") or "unknown"
    duration_minutes = stats.get("duration_minutes")
    total_samples = stats.get("total_samples", 0)

    duration_str = f"{duration_minutes} min" if duration_minutes is not None else "unknown duration"
    header_block = (
        f"Network: {wifi_ssid}\n"
        f"Time range: {start_time} to {end_time} ({duration_str}, {total_samples} samples)\n"
    )

    # Metric stats table
    metric_defs = [
        ("http_ttfb_ms", "HTTP TTFB (ms)"),
        ("ping_gateway_avg_ms", "Gateway ping (ms)"),
        ("ping_external_avg_ms", "External ping (ms)"),
        ("dns_resolution_ms", "DNS resolution (ms)"),
        ("wifi_snr_db", "WiFi SNR (dB)"),
        ("device_count", "Device count"),
        ("wifi_tx_rate_mbps", "WiFi TX rate (Mbps)"),
    ]

    lines = []
    header = f"{'Metric':<24} {'Mean':>10} {'Min':>10} {'Max':>10} {'Std':>10}"
    lines.append(header)
    lines.append("-" * len(header))

    for key, label in metric_defs:
        mean_key = f"{key}_mean"
        min_key = f"{key}_min"
        max_key = f"{key}_max"
        std_key = f"{key}_std"
        if mean_key not in stats:
            continue

        def fmt_val(v: Any) -> str:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return "NA"
            try:
                return f"{float(v):.2f}"
            except Exception:
                return "NA"

        mean = fmt_val(stats.get(mean_key))
        vmin = fmt_val(stats.get(min_key))
        vmax = fmt_val(stats.get(max_key))
        std = fmt_val(stats.get(std_key))
        line = f"{label:<24} {mean:>10} {vmin:>10} {vmax:>10} {std:>10}"
        lines.append(line)

    stats_block = "\n".join(lines)

    # Anomalies block
    if anomalies:
        anomaly_lines = []
        for a in anomalies:
            ts = a.get("timestamp", "unknown")
            metric = a.get("metric", "unknown")
            value = a.get("value", "NA")
            z = a.get("z_score", "NA")
            anomaly_lines.append(
                f"[{ts}] {metric} = {value} ({z}σ above mean)"
            )
        anomalies_block = "\n".join(anomaly_lines)
    else:
        anomalies_block = (
            f"No statistical anomalies detected (no values exceeded {Z_SCORE_THRESHOLD} standard deviations above mean)."
        )

    user_content = (
        "Network context\n"
        f"{header_block}\n"
        "Metric statistics\n"
        f"{stats_block}\n\n"
        "Anomaly events\n"
        f"{anomalies_block}"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def detect_anomalies(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Detect simple statistical anomalies based on mean + Z_SCORE_THRESHOLD*std threshold."""

    anomalies: list[dict[str, Any]] = []

    for col in METRICS:
        if col not in df.columns:
            continue

        series = pd.to_numeric(df[col], errors="coerce")
        mean = series.mean()
        std = series.std()
        if pd.isna(std) or std == 0:
            continue

        threshold = mean + Z_SCORE_THRESHOLD * std
        mask = series > threshold
        if not mask.any():
            continue

        # Skip metrics with too few or too infrequent anomalies
        if mask.sum() < 3:
            continue
        if mask.mean() < 0.02:
            continue

        for idx in df.index[mask]:
            row = df.loc[idx]
            value = row.get(col)
            if pd.isna(value):
                continue
            z_score = (value - mean) / std
            ts = row.get("timestamp")
            ts_iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            anomalies.append(
                {
                    "timestamp": ts_iso,
                    "metric": col,
                    "value": round(float(value), 2),
                    "z_score": round(float(z_score), 2),
                }
            )

    anomalies.sort(key=lambda a: a["timestamp"])
    return anomalies


@router.post("/run")
def run_analysis(request: AnalysisRequest) -> dict[str, Any]:
    """Run analysis for the given time range."""
    try:
        df = load_csv()
        if request.start_time.strip() or request.end_time.strip():
            filtered = filter_range(df, request.start_time, request.end_time)
        else:
            filtered = df
        stats = compute_stats(filtered)
        anomalies = detect_anomalies(filtered)
        prompt = build_prompt(stats, anomalies)
        response = litellm.completion(
            model=os.getenv("LANTERN_MODEL"),
            messages=prompt,
            stream=False,
        )
        summary_text = response.choices[0].message.content
        return {
            "stats": stats,
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "summary": summary_text,
        }
    except HTTPException:
        raise
    except litellm.AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key — check your .env file",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
