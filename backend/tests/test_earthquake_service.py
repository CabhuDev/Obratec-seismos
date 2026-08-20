from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from backend.app.services.earthquakes import (
    EarthquakeService,
    UpstreamFetchError,
    UpstreamUnavailableError,
)
from backend.tests.test_ign_parser import SAMPLE_FEED


@pytest.mark.asyncio
async def test_service_reuses_fresh_cached_feed() -> None:
    calls = 0

    async def fetch_text() -> str:
        nonlocal calls
        calls += 1
        return SAMPLE_FEED

    now = datetime(2026, 8, 20, 18, 0, tzinfo=UTC)
    service = EarthquakeService(fetch_text=fetch_text, cache_ttl=timedelta(minutes=2))

    first = await service.get_earthquakes("3d", now=now)
    second = await service.get_earthquakes("3d", now=now + timedelta(seconds=30))

    assert calls == 1
    assert first.earthquakes == second.earthquakes
    assert second.stale is False
    assert second.fetched_at == now


@pytest.mark.asyncio
async def test_service_returns_stale_snapshot_when_refresh_fails() -> None:
    calls = 0

    async def fetch_text() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            return SAMPLE_FEED
        raise UpstreamFetchError("IGN unavailable")

    now = datetime(2026, 8, 20, 18, 0, tzinfo=UTC)
    service = EarthquakeService(fetch_text=fetch_text, cache_ttl=timedelta(minutes=2))
    await service.get_earthquakes("3d", now=now)

    snapshot = await service.get_earthquakes("3d", now=now + timedelta(minutes=3))

    assert snapshot.stale is True
    assert snapshot.earthquakes[0]["id"] == "es2026test"


@pytest.mark.asyncio
async def test_service_does_not_queue_expired_cache_callers_after_refresh_failure() -> None:
    calls = 0
    refresh_started = asyncio.Event()
    release_refresh = asyncio.Event()

    async def fetch_text() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            return SAMPLE_FEED
        refresh_started.set()
        await release_refresh.wait()
        raise UpstreamFetchError("IGN unavailable")

    now = datetime(2026, 8, 20, 18, 0, tzinfo=UTC)
    service = EarthquakeService(
        fetch_text=fetch_text,
        cache_ttl=timedelta(minutes=2),
        upstream_retry=timedelta(seconds=30),
    )
    await service.get_earthquakes("3d", now=now)

    refreshing = asyncio.create_task(
        service.get_earthquakes("3d", now=now + timedelta(minutes=3))
    )
    await refresh_started.wait()
    concurrent = [
        asyncio.create_task(service.get_earthquakes("3d", now=now + timedelta(minutes=3)))
        for _ in range(4)
    ]
    await asyncio.sleep(0)

    assert all(task.done() for task in concurrent)
    release_refresh.set()
    snapshots = [await refreshing, *(await asyncio.gather(*concurrent))]
    snapshots.append(
        await service.get_earthquakes("3d", now=now + timedelta(minutes=3, seconds=29))
    )

    assert calls == 2
    assert all(snapshot is snapshots[0] for snapshot in snapshots)
    assert snapshots[0].stale is True


@pytest.mark.asyncio
async def test_service_returns_stale_snapshot_when_refreshed_feed_is_invalid() -> None:
    calls = 0

    async def fetch_text() -> str:
        nonlocal calls
        calls += 1
        return SAMPLE_FEED if calls == 1 else "not an IGN feed"

    now = datetime(2026, 8, 20, 18, 0, tzinfo=UTC)
    service = EarthquakeService(fetch_text=fetch_text, cache_ttl=timedelta(minutes=2))
    await service.get_earthquakes("3d", now=now)

    snapshot = await service.get_earthquakes("3d", now=now + timedelta(minutes=3))

    assert snapshot.stale is True
    assert snapshot.earthquakes[0]["id"] == "es2026test"


@pytest.mark.asyncio
async def test_service_raises_without_cached_snapshot() -> None:
    async def fetch_text() -> str:
        raise UpstreamFetchError("IGN unavailable")

    service = EarthquakeService(fetch_text=fetch_text, cache_ttl=timedelta(minutes=2))

    with pytest.raises(UpstreamUnavailableError):
        await service.get_earthquakes(
            "3d", now=datetime(2026, 8, 20, 18, 0, tzinfo=UTC)
        )


@pytest.mark.asyncio
async def test_service_does_not_retry_without_cache_during_backoff() -> None:
    calls = 0

    async def fetch_text() -> str:
        nonlocal calls
        calls += 1
        raise UpstreamFetchError("IGN unavailable")

    now = datetime(2026, 8, 20, 18, 0, tzinfo=UTC)
    service = EarthquakeService(
        fetch_text=fetch_text,
        cache_ttl=timedelta(minutes=2),
        upstream_retry=timedelta(seconds=30),
    )

    with pytest.raises(UpstreamUnavailableError):
        await service.get_earthquakes("3d", now=now)
    with pytest.raises(UpstreamUnavailableError):
        await service.get_earthquakes("3d", now=now + timedelta(seconds=29))

    assert calls == 1


@pytest.mark.asyncio
async def test_no_cache_backoff_starts_after_slow_failure_completes() -> None:
    calls = 0
    monotonic_time = [0.0]

    async def fetch_text() -> str:
        nonlocal calls
        calls += 1
        monotonic_time[0] += 45
        raise UpstreamFetchError("slow IGN failure")

    service = EarthquakeService(
        fetch_text=fetch_text,
        cache_ttl=timedelta(minutes=2),
        upstream_retry=timedelta(seconds=30),
        retry_clock=lambda: monotonic_time[0],
    )
    now = datetime(2026, 8, 20, 18, 0, tzinfo=UTC)

    with pytest.raises(UpstreamUnavailableError):
        await service.get_earthquakes("3d", now=now)
    with pytest.raises(UpstreamUnavailableError):
        await service.get_earthquakes("3d", now=now + timedelta(seconds=45))

    assert calls == 1


@pytest.mark.asyncio
async def test_cached_backoff_starts_after_slow_failure_completes() -> None:
    calls = 0
    monotonic_time = [0.0]

    async def fetch_text() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            return SAMPLE_FEED
        monotonic_time[0] += 45
        raise UpstreamFetchError("slow IGN failure")

    service = EarthquakeService(
        fetch_text=fetch_text,
        cache_ttl=timedelta(minutes=2),
        upstream_retry=timedelta(seconds=30),
        retry_clock=lambda: monotonic_time[0],
    )
    now = datetime(2026, 8, 20, 18, 0, tzinfo=UTC)
    await service.get_earthquakes("3d", now=now)

    stale = await service.get_earthquakes("3d", now=now + timedelta(minutes=3))
    repeated = await service.get_earthquakes(
        "3d", now=now + timedelta(minutes=3, seconds=45)
    )

    assert calls == 2
    assert stale is repeated
    assert repeated.stale is True


@pytest.mark.asyncio
async def test_service_coalesces_concurrent_cache_misses() -> None:
    calls = 0

    async def fetch_text() -> str:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return SAMPLE_FEED

    now = datetime(2026, 8, 20, 18, 0, tzinfo=UTC)
    service = EarthquakeService(fetch_text=fetch_text, cache_ttl=timedelta(minutes=2))

    snapshots = await asyncio.gather(
        *(service.get_earthquakes("3d", now=now) for _ in range(5))
    )

    assert calls == 1
    assert all(snapshot is snapshots[0] for snapshot in snapshots)


@pytest.mark.asyncio
async def test_service_does_not_mask_unexpected_programming_errors() -> None:
    async def fetch_text() -> str:
        raise RuntimeError("programming defect")

    service = EarthquakeService(fetch_text=fetch_text, cache_ttl=timedelta(minutes=2))

    with pytest.raises(RuntimeError, match="programming defect"):
        await service.get_earthquakes(
            "3d", now=datetime(2026, 8, 20, 18, 0, tzinfo=UTC)
        )
