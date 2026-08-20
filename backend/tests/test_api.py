from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from backend.app.main import create_app
from backend.app.services.earthquakes import EarthquakeService
from backend.tests.test_ign_parser import SAMPLE_FEED


@pytest.mark.asyncio
async def test_earthquakes_endpoint_returns_metadata_and_items() -> None:
    async def fetch_text() -> str:
        return SAMPLE_FEED

    service = EarthquakeService(fetch_text=fetch_text, cache_ttl=timedelta(minutes=2))
    app = create_app(service=service, clock=lambda: datetime(2026, 8, 20, 18, 0, tzinfo=UTC))

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/earthquakes?period=3d&min_magnitude=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"] == {
        "count": 1,
        "period": "3d",
        "stale": False,
        "fetched_at": "2026-08-20T18:00:00Z",
        "source": "Instituto Geográfico Nacional (IGN)",
    }
    assert payload["items"][0]["id"] == "es2026test"


@pytest.mark.asyncio
async def test_earthquakes_endpoint_applies_magnitude_filter() -> None:
    async def fetch_text() -> str:
        return SAMPLE_FEED

    service = EarthquakeService(fetch_text=fetch_text, cache_ttl=timedelta(minutes=2))
    app = create_app(service=service, clock=lambda: datetime(2026, 8, 20, 18, 0, tzinfo=UTC))

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/earthquakes?period=3d&min_magnitude=3")

    assert response.status_code == 200
    assert response.json()["meta"]["count"] == 0
    assert response.json()["items"] == []
