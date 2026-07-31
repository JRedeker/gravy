"""Typed runtime configuration validation tests."""

from __future__ import annotations

import pytest

from gravy.config import ConfigurationError, GravyRuntimeConfig


def test_config_defaults_to_loopback_and_mcp_path() -> None:
    config = GravyRuntimeConfig(internal_port=7654, external_port=6277)
    config.validate()
    assert config.internal_host == "127.0.0.1"
    assert config.path == "/mcp"
    assert config.internal_url == "http://127.0.0.1:7654/mcp"
    assert config.vision_url == "http://127.0.0.1:6277/mcp"


def test_config_rejects_non_loopback_host() -> None:
    with pytest.raises(ConfigurationError, match="loopback"):
        GravyRuntimeConfig(internal_host="0.0.0.0", internal_port=7654, external_port=6277).validate()


def test_config_rejects_bad_path() -> None:
    with pytest.raises(ConfigurationError, match="/mcp"):
        GravyRuntimeConfig(internal_port=7654, external_port=6277, path="/not-mcp").validate()


def test_config_rejects_internal_port_in_vision_external_range() -> None:
    for bad_port in (6276, 6300, 6325):
        with pytest.raises(ConfigurationError, match="6276"):
            GravyRuntimeConfig(internal_port=bad_port, external_port=6277).validate()


def test_config_rejects_external_port_outside_vision_range() -> None:
    for bad_port in (6275, 6326):
        with pytest.raises(ConfigurationError, match="6276"):
            GravyRuntimeConfig(internal_port=7654, external_port=bad_port).validate()


def test_config_rejects_internal_port_equal_to_external() -> None:
    with pytest.raises(ConfigurationError, match="equal"):
        GravyRuntimeConfig(internal_port=7654, external_port=7654).validate()


def test_config_rejects_missing_or_invalid_internal_port() -> None:
    with pytest.raises(ConfigurationError):
        GravyRuntimeConfig(internal_port=0, external_port=6277).validate()
    with pytest.raises(ConfigurationError):
        GravyRuntimeConfig(internal_port=70000, external_port=6277).validate()
    with pytest.raises(ConfigurationError):
        GravyRuntimeConfig(internal_port=None, external_port=6277).validate()  # type: ignore[arg-type]
