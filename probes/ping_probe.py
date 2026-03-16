import subprocess
import re
import platform
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def _parse_packet_loss(output: str) -> Optional[float]:
    patterns = [
        r"(\d+(?:\.\d+)?)%\s*packet loss",  # macOS/Linux
        r"Lost\s*=\s*\d+\s*\((\d+(?:\.\d+)?)%\s*loss\)",  # Windows
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (TypeError, ValueError):
                return None

    return None

def _parse_avg_rtt_ms(output: str) -> Optional[float]:
    patterns = [
        r"(?:round-trip|rtt)\s+min/avg/max/(?:stddev|mdev)\s*=\s*[\d.]+/([\d.]+)/",  # macOS/Linux
        r"Average\s*=\s*(\d+(?:\.\d+)?)\s*ms",  # Windows
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (TypeError, ValueError):
                return None

    return None

def ping_host(host: str, count: int) -> tuple[float, float] | None:
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, str(count), host]

    try:
        # Keep stdout/stderr available even when ping exits non-zero
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        # Any subprocess-level failure returns None metrics
        if result.returncode != 0:
            stderr_text = (result.stderr or "").strip()
            error = f"Ping command failed for {host}. Exit code: {result.returncode}."
            if stderr_text:
                error = f"{error} Details: {stderr_text}"
            logger.error(error)
            return None

        output = f"{result.stdout}\n{result.stderr}".strip()
        if not output:
            logger.error("Ping command returned no output for host=%s.", host)
            return None

        try:
            packet_loss = _parse_packet_loss(output)
            avg_rtt = _parse_avg_rtt_ms(output)
        except Exception as e:
            logger.exception("Failed to parse ping output for host=%s: %s", host, e)
            return None

        # Any parse failure returns None metrics for both values
        if packet_loss is None or avg_rtt is None:
            logger.error(
                "Failed to parse ping metrics for host=%s. packet_loss=%s, avg_rtt=%s",
                host,
                packet_loss,
                avg_rtt,
            )
            return None

        return (avg_rtt, packet_loss)

    except FileNotFoundError:
        logger.exception("The 'ping' command was not found on this system.")
        return None
    except Exception as e:
        logger.exception("Unexpected error while pinging host=%s: %s", host, e)
        return None