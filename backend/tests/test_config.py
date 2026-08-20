from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.config import Settings


@pytest.mark.parametrize(
    "url",
    [
        "http://www.ign.es/terremotos.js",
        "https://evil.example/terremotos.js",
        "https://www.ign.es.evil.example/terremotos.js",
    ],
)
def test_settings_rejects_unsafe_feed_urls(url: str) -> None:
    with pytest.raises(ValidationError, match="IGN feed URL"):
        Settings(ign_feed_url=url)


def test_settings_accepts_https_feed_host_from_configured_allowlist() -> None:
    settings = Settings(
        ign_feed_url="https://datos.example/terremotos.js",
        ign_allowed_hosts="datos.example",
    )

    assert settings.ign_feed_url == "https://datos.example/terremotos.js"


def test_upstream_retry_defaults_to_30_seconds() -> None:
    assert Settings().upstream_retry_seconds == 30


@pytest.mark.parametrize("seconds", [0, 301])
def test_upstream_retry_seconds_is_bounded(seconds: int) -> None:
    with pytest.raises(ValidationError):
        Settings(upstream_retry_seconds=seconds)
