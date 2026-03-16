"""Tests for probes.dns_probe (DNS resolution timing)."""
import socket
import pytest
from unittest.mock import MagicMock

from probes.dns_probe import ping_dns


def test_ping_dns_returns_ms_on_success(mocker):
    """Happy path: socket.gethostbyname succeeds; returns positive ms."""
    mocker.patch("probes.dns_probe.time.perf_counter", side_effect=[0.0, 0.012])
    mocker.patch("probes.dns_probe.socket.gethostbyname", return_value="93.184.216.34")
    result = ping_dns("example.com")
    assert result is not None
    assert result == 12.0  # (0.012 - 0) * 1000


def test_ping_dns_returns_none_on_gaierror(mocker):
    """Failure path: socket.gethostbyname raises socket.gaierror (e.g. NXDOMAIN)."""
    mocker.patch(
        "probes.dns_probe.socket.gethostbyname",
        side_effect=socket.gaierror(socket.EAI_NONAME, "Name or service not known"),
    )
    assert ping_dns("nonexistent.invalid") is None


def test_ping_dns_returns_none_on_other_exception(mocker):
    """Failure path: any other exception is caught and returns None."""
    mocker.patch(
        "probes.dns_probe.socket.gethostbyname",
        side_effect=OSError("Network unreachable"),
    )
    assert ping_dns("example.com") is None
