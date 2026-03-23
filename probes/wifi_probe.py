import os
import sys
import subprocess
import re
from probes import config
import logging

logger = logging.getLogger(__name__)

def _get_ssid_fallback() -> str | None:
    """Fallback for SSID on macOS Sonoma and later when system_profiler returns <redacted>."""
    try:
        result = subprocess.run(
            ['networksetup', '-getairportnetwork', 'en0'],
            capture_output=True, text=True, check=True
        )
        output = result.stdout
        ssid_match = re.search(r"Current Wi-Fi Network:\s*(.+)", output)
        if ssid_match:
            return ssid_match.group(1).strip()
        return None
    except Exception as e:
        logger.exception("Error running SSID fallback: %s", e)
        return None

def get_wifi_stats() -> dict:
    
    stats = {
        'ssid': None,
        'rssi_dbm': None,
        'noise_dbm': None,
        'snr_db': None,
        'channel': None,
        'tx_rate_mbps': None
    }

    # Branch based on the operating system
    if sys.platform == 'darwin':
        if os.path.exists(config.AIRPORT_PATH):
            result = subprocess.run(
                [config.AIRPORT_PATH, '-I'],
                capture_output=True, text=True
            )
            # airport is present but effectively dead
            if result.returncode == 0 and 'agrCtlRSSI' in result.stdout:
                _parse_airport(stats, result.stdout)
            else:
                _parse_system_profiler(stats)
        else:
            _parse_system_profiler(stats)

        # SSID privacy fallback for macOS Sonoma and later
        if stats['ssid'] is None or stats['ssid'] == '<redacted>':
            ssid_fallback = _get_ssid_fallback()
            if ssid_fallback:
                stats['ssid'] = ssid_fallback
    elif sys.platform == 'win32':
        _parse_windows_netsh(stats)
    elif sys.platform.startswith('linux'):
        _parse_linux_iw(stats)

    # Compute SNR dynamically if both dependencies were successfully parsed
    if stats['rssi_dbm'] is not None and stats['noise_dbm'] is not None:
        try:
            stats['snr_db'] = stats['rssi_dbm'] - stats['noise_dbm']
        except (TypeError, ValueError):
            pass # Keep as None if math fails

    return stats

def _parse_airport(stats: dict, output: str | None = None):
    """Parses output from the older macOS airport utility (<= macOS 13)."""
    try:
        if output is None:
            result = subprocess.run([config.AIRPORT_PATH, '-I'], capture_output=True, text=True, check=True)
            output = result.stdout

        # Match "SSID:" but specifically avoid "BSSID:"
        ssid_match = re.search(r"^\s*SSID:\s*(.+)$", output, re.MULTILINE)
        if ssid_match:
            stats['ssid'] = ssid_match.group(1).strip()

        rssi_match = re.search(r"^\s*agrCtlRSSI:\s*(-?\d+)", output, re.MULTILINE)
        if rssi_match:
            stats['rssi_dbm'] = int(rssi_match.group(1))

        noise_match = re.search(r"^\s*agrCtlNoise:\s*(-?\d+)", output, re.MULTILINE)
        if noise_match:
            stats['noise_dbm'] = int(noise_match.group(1))

        tx_match = re.search(r"^\s*lastTxRate:\s*(\d+)", output, re.MULTILINE)
        if tx_match:
            stats['tx_rate_mbps'] = int(tx_match.group(1))

        chan_match = re.search(r"^\s*channel:\s*(\d+)", output, re.MULTILINE)
        if chan_match:
            stats['channel'] = int(chan_match.group(1))

    except Exception as e:
        logger.exception("Error parsing airport output: %s", e)

def _parse_system_profiler(stats: dict, output: str | None = None):
    """Parses output from system_profiler (macOS 14+ / Sonoma). Note: Takes ~3s to run."""
    try:
        if output is None:
            result = subprocess.run(['system_profiler', 'SPAirPortDataType'], capture_output=True, text=True, check=True)
            output = result.stdout

        # Look for the section header and grab the very next indented line as the SSID
        cni_match = re.search(r"Current Network Information:\s*\n\s+([^:]+):", output)
        if cni_match:
            stats['ssid'] = cni_match.group(1).strip()

        # Signal / Noise usually appears as: "Signal / Noise: -45 dBm / -90 dBm"
        sig_noise_match = re.search(r"Signal / Noise:\s*(-?\d+)\s*dBm\s*/\s*(-?\d+)\s*dBm", output)
        if sig_noise_match:
            stats['rssi_dbm'] = int(sig_noise_match.group(1))
            stats['noise_dbm'] = int(sig_noise_match.group(2))

        # Channel usually appears as "Channel: 36 (5 GHz, 80MHz)"
        chan_match = re.search(r"Channel:\s*(\d+)", output)
        if chan_match:
            stats['channel'] = int(chan_match.group(1))

        tx_match = re.search(r"Transmit Rate:\s*(\d+)", output)
        if tx_match:
            stats['tx_rate_mbps'] = int(tx_match.group(1))

    except Exception as e:
        logger.exception("Error parsing system_profiler output: %s", e)

def _parse_windows_netsh(stats: dict):
    """Basic fallback parser for Windows."""
    try:
        result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True, check=True)
        output = result.stdout

        ssid_match = re.search(r"^\s*SSID\s*:\s*(.+)$", output, re.MULTILINE)
        if ssid_match:
            stats['ssid'] = ssid_match.group(1).strip()

        chan_match = re.search(r"^\s*Channel\s*:\s*(\d+)", output, re.MULTILINE)
        if chan_match:
            stats['channel'] = int(chan_match.group(1))

        tx_match = re.search(r"^\s*Transmit rate \(Mbps\)\s*:\s*(\d+)", output, re.MULTILINE)
        if tx_match:
            stats['tx_rate_mbps'] = int(tx_match.group(1))

        # Windows gives Signal Quality as a percentage, not RSSI/Noise in dBm
        # A rough approximation formula is (Signal % / 2) - 100
        sig_match = re.search(r"^\s*Signal\s*:\s*(\d+)%", output, re.MULTILINE)
        if sig_match:
            stats['rssi_dbm'] = int((int(sig_match.group(1)) / 2) - 100)

    except Exception as e:
        logger.exception("Error parsing netsh output: %s", e)

def _parse_linux_iw(stats: dict):
    """Basic fallback parser for Linux (assumes iwconfig is available)."""
    try:
        result = subprocess.run(['iwconfig'], capture_output=True, text=True, check=True)
        output = result.stdout

        ssid_match = re.search(r'ESSID:"([^"]+)"', output)
        if ssid_match:
            stats['ssid'] = ssid_match.group(1).strip()

        # Format varies, but often looks like: "Signal level=-45 dBm  Noise level=-90 dBm"
        sig_match = re.search(r"Signal level=(-?\d+)", output)
        if sig_match:
            stats['rssi_dbm'] = int(sig_match.group(1))

        noise_match = re.search(r"Noise level=(-?\d+)", output)
        if noise_match:
            stats['noise_dbm'] = int(noise_match.group(1))

        tx_match = re.search(r"Bit Rate[=:](\d+)", output)
        if tx_match:
            stats['tx_rate_mbps'] = int(tx_match.group(1))

    except Exception as e:
        logger.exception("Error parsing iwconfig output: %s", e)