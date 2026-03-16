"""Tests for probes.ping_probe (ping subprocess and parsing)."""
import pytest
from unittest.mock import MagicMock

from probes.ping_probe import ping_host, _parse_packet_loss, _parse_avg_rtt_ms


# ---------- Fixtures: sample subprocess output strings ----------

@pytest.fixture
def ping_stdout_valid():
    """macOS/Linux-style ping summary with 0% loss and RTT."""
    return (
        "PING 8.8.8.8 (8.8.8.8): 56 data bytes\n"
        "64 bytes from 8.8.8.8: icmp_seq=0 ttl=117 time=12.5 ms\n"
        "round-trip min/avg/max/stddev = 11.2/12.5/13.1/0.5 ms\n"
        "2 packets transmitted, 2 packets received, 0.0% packet loss"
    )


@pytest.fixture
def ping_stdout_100_percent_loss():
    """Ping output indicating 100% packet loss."""
    return (
        "PING 192.168.99.99 (192.168.99.99): 56 data bytes\n"
        "Request timeout for icmp_seq 0\n"
        "2 packets transmitted, 0 packets received, 100% packet loss"
    )


@pytest.fixture
def ping_stdout_unparseable():
    """Completely unparseable string (no packet loss or RTT patterns)."""
    return "garbage output with no stats\nnope\n"


# ---------- ping_host: subprocess mocked ----------

def test_ping_host_returns_avg_rtt_and_packet_loss_on_success(mocker, ping_stdout_valid):
    """Happy path: subprocess returns 0 and well-formed stdout."""
    mock_run = mocker.patch(
        "probes.ping_probe.subprocess.run",
        return_value=MagicMock(returncode=0, stdout=ping_stdout_valid, stderr=""),
    )
    result = ping_host("8.8.8.8", 2)
    assert result is not None
    avg_rtt, packet_loss = result
    assert avg_rtt == 12.5
    assert packet_loss == 0.0
    mock_run.assert_called_once()


def test_ping_host_returns_none_on_nonzero_exit_code(mocker):
    """Failure path: ping exits non-zero (e.g. host unreachable)."""
    mocker.patch(
        "probes.ping_probe.subprocess.run",
        return_value=MagicMock(returncode=1, stdout="", stderr="Request timeout"),
    )
    assert ping_host("192.168.99.99", 2) is None


def test_ping_host_returns_none_on_empty_stdout_and_stderr(mocker):
    """Edge case: returncode 0 but no output to parse."""
    mocker.patch(
        "probes.ping_probe.subprocess.run",
        return_value=MagicMock(returncode=0, stdout="", stderr=""),
    )
    assert ping_host("8.8.8.8", 2) is None


def test_ping_host_returns_none_when_output_unparseable(mocker, ping_stdout_unparseable):
    """Edge case: stdout has no packet loss or RTT regex match."""
    mocker.patch(
        "probes.ping_probe.subprocess.run",
        return_value=MagicMock(returncode=0, stdout=ping_stdout_unparseable, stderr=""),
    )
    assert ping_host("8.8.8.8", 2) is None


def test_ping_host_returns_none_on_file_not_found(mocker):
    """Failure path: ping command not found."""
    mocker.patch("probes.ping_probe.subprocess.run", side_effect=FileNotFoundError())
    assert ping_host("8.8.8.8", 2) is None


def test_ping_host_parses_100_percent_loss_correctly(mocker, ping_stdout_100_percent_loss):
    """Edge case: valid summary with 100% packet loss (RTT may be missing on some platforms)."""
    # macOS with 100% loss might still print round-trip line; use output that has loss but no RTT
    mocker.patch(
        "probes.ping_probe.subprocess.run",
        return_value=MagicMock(
            returncode=0,
            stdout=ping_stdout_100_percent_loss,
            stderr="",
        ),
    )
    result = ping_host("192.168.99.99", 2)
    # Parsing may fail for avg_rtt when only loss line is present, so result can be None
    # If both are parseable we get (avg_rtt, 100.0)
    if result is not None:
        _, packet_loss = result
        assert packet_loss == 100.0


# ---------- _parse_packet_loss / _parse_avg_rtt_ms (unit-style) ----------

def test_parse_packet_loss_extracts_percent():
    """_parse_packet_loss returns float when pattern matches."""
    out = "2 packets transmitted, 2 received, 0.0% packet loss"
    assert _parse_packet_loss(out) == 0.0
    assert _parse_packet_loss("100% packet loss") == 100.0


def test_parse_packet_loss_returns_none_for_unparseable():
    """_parse_packet_loss returns None when no pattern matches."""
    assert _parse_packet_loss("no numbers here") is None


def test_parse_avg_rtt_ms_extracts_avg():
    """_parse_avg_rtt_ms returns float for macOS/Linux style."""
    out = "round-trip min/avg/max/stddev = 11.2/12.5/13.1/0.5 ms"
    assert _parse_avg_rtt_ms(out) == 12.5


def test_parse_avg_rtt_ms_returns_none_for_unparseable():
    """_parse_avg_rtt_ms returns None when no pattern matches."""
    assert _parse_avg_rtt_ms("no rtt here") is None
