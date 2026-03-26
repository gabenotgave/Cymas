"""Analysis endpoints for Cymas metrics."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import litellm
import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.routers.metrics import load_csv

load_dotenv()

litellm.drop_params = True

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

METRIC_LABELS: dict[str, str] = {
    "http_ttfb_ms": "HTTP TTFB",
    "ping_gateway_avg_ms": "Gateway Ping",
    "ping_external_avg_ms": "External Ping",
    "dns_resolution_ms": "DNS Resolution",
    "wifi_snr_db": "WiFi SNR",
    "device_count": "Device Count",
    "wifi_tx_rate_mbps": "WiFi TX Rate",
}

# Per-metric anomaly detection config: z-score threshold, absolute floor, and direction
METRIC_THRESHOLDS: dict[str, dict[str, Any]] = {
    "http_ttfb_ms":          {"z": 2.5, "abs_floor": 300,  "direction": "high"},
    "ping_gateway_avg_ms":   {"z": 2.5, "abs_floor": 50,   "direction": "high"},
    "ping_external_avg_ms":  {"z": 2.5, "abs_floor": 100,  "direction": "high"},
    "dns_resolution_ms":     {"z": 2.5, "abs_floor": 200,  "direction": "high"},
    "wifi_snr_db":           {"z": 2.5, "abs_floor": 15,   "direction": "low"},
    "device_count":          {"z": 3.0, "abs_floor": None, "direction": "high"},
    "wifi_tx_rate_mbps":     {"z": 2.5, "abs_floor": None, "direction": "low"},
}

MIN_CONSECUTIVE_SAMPLES = 2
MIN_ANOMALY_FRACTION = 0.001
CLUSTER_GAP_MINUTES = 30
MAX_FINDINGS_FOR_LLM = 15
MAX_WEAK_SIGNALS = 50


class AnalysisRequest(BaseModel):
    start_time: str
    end_time: str


def filter_range(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Filter dataframe to rows between start and end timestamps."""
    if "timestamp" not in df.columns:
        raise HTTPException(status_code=400, detail="No timestamp column found in data")

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
    return value


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


def _anomaly_mask(series: pd.Series, cfg: dict[str, Any]) -> pd.Series:
    """Return a boolean Series flagging anomalous values per metric config."""
    numeric = pd.to_numeric(series, errors="coerce")
    mean = numeric.mean()
    std = numeric.std()

    if pd.isna(std) or std == 0:
        return pd.Series(False, index=series.index)

    direction = cfg["direction"]
    z = cfg["z"]
    abs_floor = cfg.get("abs_floor")

    if direction == "high":
        stat_mask = numeric > (mean + z * std)
        if abs_floor is not None:
            stat_mask = stat_mask & (numeric > abs_floor)
    else:  # "low"
        stat_mask = numeric < (mean - z * std)
        if abs_floor is not None:
            stat_mask = stat_mask & (numeric < abs_floor)

    return stat_mask.fillna(False)


def _find_runs(mask: pd.Series) -> list[tuple[int, int]]:
    """Return list of (start_iloc, end_iloc) for each consecutive True run."""
    runs: list[tuple[int, int]] = []
    values = mask.to_numpy()
    n = len(values)
    i = 0
    while i < n:
        if values[i]:
            j = i
            while j < n and values[j]:
                j += 1
            runs.append((i, j - 1))
            i = j
        else:
            i += 1
    return runs


@dataclass
class AnomalyEvent:
    metric: str
    label: str
    start_ts: pd.Timestamp
    end_ts: pd.Timestamp
    peak_value: float
    mean_value: float
    std_value: float
    sample_count: int
    is_single_spike: bool

    @property
    def z_score(self) -> float:
        if self.std_value == 0:
            return 0.0
        return round((self.peak_value - self.mean_value) / self.std_value, 2)

    @property
    def confidence(self) -> str:
        if self.sample_count >= 5:
            return "High"
        if self.is_single_spike:
            return "Low"
        return "Medium"

    def time_str(self) -> str:
        def _fmt(ts: pd.Timestamp) -> str:
            day = ts.strftime("%d").lstrip("0") or "0"
            hour = ts.strftime("%I").lstrip("0") or "12"
            return ts.strftime(f"%A %B {day}, %Y at {hour}:%M %p UTC")

        start_s = _fmt(self.start_ts)
        if self.start_ts == self.end_ts:
            return start_s
        return f"{start_s} to {_fmt(self.end_ts)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "label": self.label,
            "start_ts": self.start_ts.isoformat(),
            "end_ts": self.end_ts.isoformat(),
            "peak_value": self.peak_value,
            "mean_value": self.mean_value,
            "std_value": self.std_value,
            "sample_count": self.sample_count,
            "is_single_spike": self.is_single_spike,
            "z_score": self.z_score,
            "confidence": self.confidence,
            "time_str": self.time_str(),
        }


def detect_anomalies(df: pd.DataFrame) -> tuple[list[AnomalyEvent], list[AnomalyEvent]]:
    """Detect anomalies per metric. Returns (findings, weak_signals)."""
    findings: list[AnomalyEvent] = []
    weak_signals: list[AnomalyEvent] = []

    for metric, cfg in METRIC_THRESHOLDS.items():
        if metric not in df.columns:
            continue

        series = pd.to_numeric(df[metric], errors="coerce")
        mean_val = float(series.mean())
        std_val = float(series.std()) if not pd.isna(series.std()) else 0.0

        mask = _anomaly_mask(df[metric], cfg)

        if mask.mean() < MIN_ANOMALY_FRACTION:
            continue

        runs = _find_runs(mask)
        label = METRIC_LABELS.get(metric, metric)

        for start_iloc, end_iloc in runs:
            run_series = series.iloc[start_iloc : end_iloc + 1]
            timestamps = df["timestamp"].iloc[start_iloc : end_iloc + 1]
            sample_count = end_iloc - start_iloc + 1
            is_single_spike = sample_count < MIN_CONSECUTIVE_SAMPLES

            if cfg["direction"] == "high":
                peak_value = float(run_series.max())
            else:
                peak_value = float(run_series.min())

            event = AnomalyEvent(
                metric=metric,
                label=label,
                start_ts=timestamps.iloc[0],
                end_ts=timestamps.iloc[-1],
                peak_value=round(peak_value, 2),
                mean_value=round(mean_val, 2),
                std_value=round(std_val, 2),
                sample_count=sample_count,
                is_single_spike=is_single_spike,
            )

            if sample_count < MIN_CONSECUTIVE_SAMPLES:
                weak_signals.append(event)
            else:
                findings.append(event)

    findings.sort(key=lambda e: e.start_ts)
    weak_signals.sort(key=lambda e: e.start_ts)
    return findings, weak_signals


SYSTEM_PROMPT = """You are a network diagnostics assistant. You will receive pre-structured findings from an automated anomaly detector. Your only job is to write the output sections described below.

STRICT RULES:
- Do not invent, add, remove, or reorder findings.
- Do not invent timestamps or values. Copy timestamps exactly as given.
- Do not add commentary, analysis, or context beyond what is provided.
- Produce plain text only. No markdown, no asterisks, no HTML, no special characters.
- Follow the output format exactly. Every label must appear on its own line.

OUTPUT FORMAT:

SUMMARY
Write 2-3 sentences summarizing the overall network health based only on the findings provided.

FINDINGS
FINDING: One plain-English sentence describing the finding.
METRICS: The affected metric label.
TIME: Copy the timestamp exactly as given.
CONFIDENCE: Copy the confidence level exactly as given.

RECOMMENDATIONS
ACTION: One specific actionable recommendation based on the findings.

If findings is empty write "None." under FINDINGS. If no findings exist write "None." under RECOMMENDATIONS."""


def _format_events_for_prompt(events: list[AnomalyEvent]) -> str:
    """Format a list of AnomalyEvent into a numbered plain-text block."""
    if not events:
        return "None."
    lines = []
    for i, e in enumerate(events, 1):
        lines.append(
            f"{i}. {e.label} | Time: {e.time_str()} | Peak: {e.peak_value} | "
            f"Baseline mean: {e.mean_value} | Z-score: {e.z_score} | "
            f"Consecutive samples: {e.sample_count} | Confidence: {e.confidence}"
        )
    return "\n".join(lines)


def cluster_findings(findings: list[AnomalyEvent]) -> list[AnomalyEvent]:
    """Merge findings of the same metric whose time ranges are within CLUSTER_GAP_MINUTES."""
    if not findings:
        return []

    # Group by metric
    groups: dict[str, list[AnomalyEvent]] = {}
    for event in findings:
        groups.setdefault(event.metric, []).append(event)

    clustered: list[AnomalyEvent] = []
    gap = pd.Timedelta(minutes=CLUSTER_GAP_MINUTES)

    for metric, events in groups.items():
        events = sorted(events, key=lambda e: e.start_ts)
        direction = METRIC_THRESHOLDS.get(metric, {}).get("direction", "high")

        merged = [events[0]]
        for event in events[1:]:
            prev = merged[-1]
            if (event.start_ts - prev.end_ts) <= gap:
                # Merge into prev
                if direction == "high":
                    new_peak = max(prev.peak_value, event.peak_value)
                else:
                    new_peak = min(prev.peak_value, event.peak_value)
                merged[-1] = AnomalyEvent(
                    metric=prev.metric,
                    label=prev.label,
                    start_ts=prev.start_ts,
                    end_ts=max(prev.end_ts, event.end_ts),
                    peak_value=new_peak,
                    mean_value=prev.mean_value,
                    std_value=prev.std_value,
                    sample_count=prev.sample_count + event.sample_count,
                    is_single_spike=False,
                )
            else:
                merged.append(event)

        clustered.extend(merged)

    clustered.sort(key=lambda e: e.start_ts)
    return clustered


def build_prompt(
    stats: dict[str, Any],
    findings: list[AnomalyEvent],
) -> list[dict[str, str]]:
    """Build a LiteLLM-compatible messages list from stats and findings."""
    wifi_ssid = stats.get("wifi_ssid") or "unknown"
    start_time = stats.get("start_time") or "unknown"
    end_time = stats.get("end_time") or "unknown"
    duration_minutes = stats.get("duration_minutes")
    total_samples = stats.get("total_samples", 0)

    duration_str = f"{duration_minutes} min" if duration_minutes is not None else "unknown duration"

    findings_block = _format_events_for_prompt(findings)

    user_content = (
        f"Network: {wifi_ssid}\n"
        f"Time range: {start_time} to {end_time} ({duration_str}, {total_samples} samples)\n\n"
        f"FINDINGS ({len(findings)} detected)\n"
        f"{findings_block}"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


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
        findings, weak_signals = detect_anomalies(filtered)
        findings = cluster_findings(findings)
        if len(findings) > MAX_FINDINGS_FOR_LLM:
            findings = sorted(findings, key=lambda e: e.z_score, reverse=True)[:MAX_FINDINGS_FOR_LLM]
            findings.sort(key=lambda e: e.start_ts)
        if len(weak_signals) > MAX_WEAK_SIGNALS:
            weak_signals = sorted(weak_signals, key=lambda e: e.z_score, reverse=True)[:MAX_WEAK_SIGNALS]
            weak_signals.sort(key=lambda e: e.start_ts)
        prompt = build_prompt(stats, findings)
        response = litellm.completion(
            model=os.getenv("CYMAS_MODEL"),
            messages=prompt,
            stream=False,
            temperature=0,
            seed=42,
        )
        summary_text = response.choices[0].message.content
        model_used = os.getenv("CYMAS_MODEL", "AI")
        return {
            "stats": stats,
            "model": model_used,
            "anomalies": [e.to_dict() for e in findings],
            "anomaly_count": len(findings),
            "finding_count": len(findings),
            "weak_signal_count": len(weak_signals),
            "weak_signals": [e.to_dict() for e in weak_signals],
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
