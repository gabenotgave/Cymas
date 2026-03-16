"""Tests for probes.gateway (default gateway via netifaces)."""
import pytest
import netifaces

from probes.gateway import get_default_gateway_netifaces


def test_get_default_gateway_returns_ip_when_netifaces_has_default(mocker):
    """Happy path: netifaces returns a default IPv4 gateway."""
    gateways = {
        "default": {
            netifaces.AF_INET: ("192.168.1.1", "en0"),
        },
    }
    mocker.patch("probes.gateway.netifaces.gateways", return_value=gateways)
    assert get_default_gateway_netifaces() == "192.168.1.1"


def test_get_default_gateway_returns_none_when_no_default_key(mocker):
    """Failure path: netifaces returns gateways but no 'default' key."""
    mocker.patch("probes.gateway.netifaces.gateways", return_value={"en0": []})
    assert get_default_gateway_netifaces() is None


def test_get_default_gateway_returns_none_when_empty_gateways(mocker):
    """Failure path: netifaces returns empty dict."""
    mocker.patch("probes.gateway.netifaces.gateways", return_value={})
    assert get_default_gateway_netifaces() is None


def test_get_default_gateway_returns_none_when_no_af_inet(mocker):
    """Edge case: default exists but no AF_INET entry."""
    gateways = {"default": {}}
    mocker.patch("probes.gateway.netifaces.gateways", return_value=gateways)
    assert get_default_gateway_netifaces() is None


def test_get_default_gateway_returns_none_when_gateway_ip_empty(mocker):
    """Edge case: default_info exists but gateway IP is falsy."""
    gateways = {"default": {netifaces.AF_INET: ("", "en0")}}
    mocker.patch("probes.gateway.netifaces.gateways", return_value=gateways)
    assert get_default_gateway_netifaces() is None


def test_get_default_gateway_returns_none_on_exception(mocker):
    """Failure path: netifaces.gateways raises (e.g. KeyError, TypeError)."""
    mocker.patch("probes.gateway.netifaces.gateways", side_effect=RuntimeError("netifaces failed"))
    assert get_default_gateway_netifaces() is None
