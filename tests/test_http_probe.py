"""Tests for probes.http_probe (HTTP TTFB via urllib)."""
import socket
import pytest
from unittest.mock import MagicMock

import urllib.error

from probes.http_probe import probe_http


def test_probe_http_returns_ms_on_success(mocker):
    """Happy path: urlopen succeeds, returns TTFB in ms."""
    mocker.patch("probes.http_probe.time.perf_counter", side_effect=[0.0, 0.085])
    mock_resp = MagicMock()
    mocker.patch("probes.http_probe.urllib.request.urlopen", return_value=mock_resp)
    result = probe_http("https://www.google.com")
    assert result is not None
    assert result == 85.0  # (0.085 - 0) * 1000
    mock_resp.read.assert_called_once_with(1)


def test_probe_http_returns_none_on_urlerror(mocker):
    """Failure path: urlopen raises urllib.error.URLError."""
    mocker.patch(
        "probes.http_probe.urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    )
    assert probe_http("https://localhost:9999") is None


def test_probe_http_returns_none_on_socket_timeout(mocker):
    """Failure path: urlopen raises socket.timeout (timeout)."""
    mocker.patch(
        "probes.http_probe.urllib.request.urlopen",
        side_effect=socket.timeout("timed out"),
    )
    assert probe_http("https://www.google.com") is None


def test_probe_http_returns_none_on_generic_exception(mocker):
    """Failure path: any other exception returns None."""
    mocker.patch(
        "probes.http_probe.urllib.request.urlopen",
        side_effect=ValueError("unexpected"),
    )
    assert probe_http("https://www.google.com") is None
