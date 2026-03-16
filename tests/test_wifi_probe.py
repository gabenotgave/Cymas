"""Tests for probes.wifi_probe (WiFi stats: airport, system_profiler, SNR)."""
import sys
import pytest
from unittest.mock import MagicMock

from probes import wifi_probe


# ---------- Fixtures: raw output strings for parsers ----------

@pytest.fixture
def airport_output_valid():
    """Raw airport -I style output with SSID, agrCtlRSSI, agrCtlNoise, channel, lastTxRate."""
    return (
        "     agrCtlRSSI: -52\n"
        "     agrCtlNoise: -90\n"
        "     SSID: MyHomeWiFi\n"
        "     BSSID: aa:bb:cc:dd:ee:ff\n"
        "     channel: 36\n"
        "     lastTxRate: 867\n"
    )


@pytest.fixture
def airport_output_no_rssi():
    """Airport output without agrCtlRSSI (triggers system_profiler branch)."""
    return "     SSID: SomeNet\n     channel: 6\n"


@pytest.fixture
def system_profiler_output_valid():
    """Raw system_profiler SPAirPortDataType style output."""
    return (
        "Current Network Information:\n"
        "    MyHomeWiFi:\n"
        "Signal / Noise: -45 dBm / -88 dBm\n"
        "Channel: 36 (5 GHz, 80MHz)\n"
        "Transmit Rate: 867\n"
    )


@pytest.fixture
def system_profiler_output_minimal():
    """Minimal system_profiler output (missing some fields)."""
    return "Current Network Information:\n    OnlySSID:\n"


# ---------- _parse_airport: pass raw fixture strings directly (no subprocess) ----------

def test_parse_airport_populates_stats_from_valid_output(airport_output_valid):
    """Happy path: _parse_airport with well-formed airport output (raw string passed directly)."""
    stats = {
        "ssid": None,
        "rssi_dbm": None,
        "noise_dbm": None,
        "snr_db": None,
        "channel": None,
        "tx_rate_mbps": None,
    }
    wifi_probe._parse_airport(stats, airport_output_valid)
    assert stats["ssid"] == "MyHomeWiFi"
    assert stats["rssi_dbm"] == -52
    assert stats["noise_dbm"] == -90
    assert stats["channel"] == 36
    assert stats["tx_rate_mbps"] == 867


def test_parse_airport_handles_malformed_output_gracefully():
    """Edge case: airport output with no regex matches leaves stats unchanged."""
    stats = {
        "ssid": None,
        "rssi_dbm": None,
        "noise_dbm": None,
        "snr_db": None,
        "channel": None,
        "tx_rate_mbps": None,
    }
    wifi_probe._parse_airport(stats, "garbage\nno SSID or RSSI\n")
    assert stats["ssid"] is None
    assert stats["rssi_dbm"] is None
    assert stats["noise_dbm"] is None


def test_parse_airport_does_not_raise_on_subprocess_exception(mocker):
    """Failure path: when no output passed, subprocess.run raises; parser does not propagate."""
    mocker.patch(
        "probes.wifi_probe.subprocess.run",
        side_effect=FileNotFoundError("airport not found"),
    )
    stats = {"ssid": None, "rssi_dbm": None, "noise_dbm": None, "snr_db": None, "channel": None, "tx_rate_mbps": None}
    wifi_probe._parse_airport(stats)  # no output -> runs subprocess; no raise
    assert stats["ssid"] is None


# ---------- _parse_system_profiler: pass raw fixture strings directly (no subprocess) ----------

def test_parse_system_profiler_populates_stats_from_valid_output(system_profiler_output_valid):
    """Happy path: _parse_system_profiler with well-formed output (raw string passed directly)."""
    stats = {
        "ssid": None,
        "rssi_dbm": None,
        "noise_dbm": None,
        "snr_db": None,
        "channel": None,
        "tx_rate_mbps": None,
    }
    wifi_probe._parse_system_profiler(stats, system_profiler_output_valid)
    assert stats["ssid"] == "MyHomeWiFi"
    assert stats["rssi_dbm"] == -45
    assert stats["noise_dbm"] == -88
    assert stats["channel"] == 36
    assert stats["tx_rate_mbps"] == 867


def test_parse_system_profiler_handles_minimal_output(system_profiler_output_minimal):
    """Edge case: only SSID present; other fields stay None."""
    stats = {
        "ssid": None,
        "rssi_dbm": None,
        "noise_dbm": None,
        "snr_db": None,
        "channel": None,
        "tx_rate_mbps": None,
    }
    wifi_probe._parse_system_profiler(stats, system_profiler_output_minimal)
    assert stats["ssid"] == "OnlySSID"
    assert stats["rssi_dbm"] is None
    assert stats["noise_dbm"] is None


# ---------- get_wifi_stats: branches and SNR ----------

def test_get_wifi_stats_branches_to_system_profiler_when_airport_has_no_agrCtlRSSI(mocker, airport_output_no_rssi):
    """When airport output contains no agrCtlRSSI, get_wifi_stats uses system_profiler."""
    mocker.patch.object(sys, "platform", "darwin")
    mocker.patch("probes.wifi_probe.os.path.exists", return_value=True)
    mocker.patch(
        "probes.wifi_probe.subprocess.run",
        side_effect=[
            MagicMock(returncode=0, stdout=airport_output_no_rssi, stderr=""),
            MagicMock(
                returncode=0,
                stdout="Current Network Information:\n    FallbackSSID:\nSignal / Noise: -50 dBm / -85 dBm\nChannel: 11\nTransmit Rate: 144\n",
                stderr="",
            ),
        ],
    )
    mocker.patch("probes.wifi_probe._get_ssid_fallback", return_value=None)
    stats = wifi_probe.get_wifi_stats()
    assert stats["ssid"] == "FallbackSSID"
    assert stats["rssi_dbm"] == -50
    assert stats["noise_dbm"] == -85
    assert stats["snr_db"] == 35  # -50 - (-85)


def test_get_wifi_stats_replaces_ssid_when_redacted(mocker, airport_output_valid):
    """stats['ssid'] is replaced when it equals the string '<redacted>' (SSID privacy fallback)."""
    mocker.patch.object(sys, "platform", "darwin")
    mocker.patch("probes.wifi_probe.os.path.exists", return_value=True)
    # Airport returns SSID as <redacted> (e.g. Sonoma)
    redacted_airport = (
        "     agrCtlRSSI: -52\n"
        "     agrCtlNoise: -90\n"
        "     SSID: <redacted>\n"
        "     channel: 36\n"
        "     lastTxRate: 867\n"
    )
    mocker.patch(
        "probes.wifi_probe.subprocess.run",
        side_effect=[
            MagicMock(returncode=0, stdout=redacted_airport, stderr=""),
            MagicMock(stdout="Current Wi-Fi Network: MyRealSSID\n", returncode=0, stderr=""),
        ],
    )
    mocker.patch("probes.wifi_probe._get_ssid_fallback", return_value="MyRealSSID")
    stats = wifi_probe.get_wifi_stats()
    assert stats["ssid"] == "MyRealSSID"


def test_snr_computed_as_rssi_minus_noise(mocker, airport_output_valid):
    """SNR is correctly computed as rssi_dbm - noise_dbm when both present."""
    mocker.patch.object(sys, "platform", "darwin")
    mocker.patch("probes.wifi_probe.os.path.exists", return_value=True)
    mocker.patch(
        "probes.wifi_probe.subprocess.run",
        return_value=MagicMock(returncode=0, stdout=airport_output_valid, stderr=""),
    )
    mocker.patch("probes.wifi_probe._get_ssid_fallback", return_value=None)
    stats = wifi_probe.get_wifi_stats()
    assert stats["rssi_dbm"] == -52
    assert stats["noise_dbm"] == -90
    assert stats["snr_db"] == 38  # -52 - (-90)


def test_snr_stays_none_when_noise_missing(mocker):
    """snr_db stays None if noise_dbm is missing (rssi only)."""
    mocker.patch.object(sys, "platform", "darwin")
    mocker.patch("probes.wifi_probe.os.path.exists", return_value=True)
    mocker.patch(
        "probes.wifi_probe.subprocess.run",
        return_value=MagicMock(
            returncode=0,
            stdout="     agrCtlRSSI: -52\n     SSID: X\n     channel: 1\n",
            stderr="",
        ),
    )
    mocker.patch("probes.wifi_probe._get_ssid_fallback", return_value=None)
    stats = wifi_probe.get_wifi_stats()
    assert stats["rssi_dbm"] == -52
    assert stats["noise_dbm"] is None
    assert stats["snr_db"] is None
