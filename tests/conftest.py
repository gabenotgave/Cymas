"""Shared pytest fixtures for Cymas test suite."""
import pytest

from data_io.writer import FIELDNAMES


@pytest.fixture
def sample_row():
    """A fully populated dict matching all FIELDNAMES with realistic dummy values."""
    return {
        "timestamp": "2025-03-15T12:00:00",
        "gateway_ip": "192.168.1.1",
        "device_count": 5,
        "ping_gateway_avg_ms": 2.5,
        "ping_gateway_loss_pct": 0.0,
        "ping_external_avg_ms": 18.3,
        "ping_external_loss_pct": 0.0,
        "dns_resolution_ms": 12.0,
        "http_ttfb_ms": 85.0,
        "wifi_ssid": "MyNetwork",
        "wifi_rssi_dbm": -52,
        "wifi_noise_dbm": -90,
        "wifi_snr_db": 38,
        "wifi_channel": 36,
        "wifi_tx_rate_mbps": 867,
    }
