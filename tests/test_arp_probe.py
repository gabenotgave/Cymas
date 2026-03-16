"""Tests for probes.arp_probe (ARP cache device count)."""
import pytest
from unittest.mock import MagicMock

from probes.arp_probe import get_active_device_count


@pytest.fixture
def arp_stdout_mixed():
    """arp -a -n output with complete and (incomplete) entries."""
    return (
        "? (192.168.1.1) at aa:bb:cc:dd:ee:01 on en0 ifscope [ethernet]\n"
        "? (192.168.1.10) at (incomplete) on en0 ifscope [ethernet]\n"
        "? (192.168.1.20) at 11:22:33:44:55:66 on en0 ifscope [ethernet]\n"
        "? (192.168.1.30) at (incomplete) on en0 ifscope [ethernet]\n"
    )


def test_arp_returns_count_of_complete_entries_only(mocker, arp_stdout_mixed):
    """Happy path: only lines with '(' and without '(incomplete)' are counted."""
    mocker.patch(
        "probes.arp_probe.subprocess.run",
        return_value=MagicMock(stdout=arp_stdout_mixed, returncode=0, check=True),
    )
    result = get_active_device_count()
    assert result == 2  # 192.168.1.1 and 192.168.1.20


def test_arp_returns_zero_when_no_entries(mocker):
    """Edge case: empty or no valid lines."""
    mocker.patch(
        "probes.arp_probe.subprocess.run",
        return_value=MagicMock(stdout="", returncode=0, check=True),
    )
    result = get_active_device_count()
    assert result == 0


def test_arp_returns_none_on_called_process_error(mocker):
    """Failure path: subprocess raises CalledProcessError."""
    import subprocess
    mocker.patch(
        "probes.arp_probe.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "arp"),
    )
    assert get_active_device_count() is None


def test_arp_returns_none_on_file_not_found(mocker):
    """Failure path: arp command not found."""
    mocker.patch(
        "probes.arp_probe.subprocess.run",
        side_effect=FileNotFoundError("arp not found"),
    )
    assert get_active_device_count() is None


def test_arp_returns_none_on_generic_exception(mocker):
    """Failure path: any other exception returns None."""
    mocker.patch(
        "probes.arp_probe.subprocess.run",
        side_effect=RuntimeError("unexpected"),
    )
    assert get_active_device_count() is None
