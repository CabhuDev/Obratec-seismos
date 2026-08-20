from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from backend.app.services.ign_parser import IgnFeedParseError, parse_ign_feed

PERIOD_COLLECTIONS = {"3d": "dias3", "10d": "dias10", "30d": "dias30"}


class UpstreamUnavailableError(RuntimeError):
    """Raised when the IGN feed is unavailable and no cache exists."""


class UpstreamFetchError(RuntimeError):
    """Raised when the configured IGN feed cannot be fetched safely."""


@dataclass(frozen=True, slots=True)
class EarthquakeSnapshot:
    earthquakes: list[dict[str, object]]
    fetched_at: datetime
    stale: bool = False


class EarthquakeService:
    def __init__(
        self,
        *,
        fetch_text: Callable[[], Awaitable[str]],
        cache_ttl: timedelta,
        upstream_retry: timedelta = timedelta(seconds=30),
        retry_clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fetch_text = fetch_text
        self._cache_ttl = cache_ttl
        self._upstream_retry = upstream_retry
        self._retry_clock = retry_clock
        self._cache: dict[str, EarthquakeSnapshot] = {}
        self._refresh_locks = {period: asyncio.Lock() for period in PERIOD_COLLECTIONS}
        self._retry_after: dict[str, float] = {}

    async def get_earthquakes(self, period: str, *, now: datetime) -> EarthquakeSnapshot:
        try:
            collection = PERIOD_COLLECTIONS[period]
        except KeyError as exc:
            raise ValueError(f"Unsupported period: {period}") from exc

        cached = self._cache.get(period)
        if cached and now - cached.fetched_at < self._cache_ttl:
            return cached

        retry_after = self._retry_after.get(period)
        if retry_after and self._retry_clock() < retry_after:
            if cached:
                return cached
            raise UpstreamUnavailableError("IGN earthquake data is unavailable")

        refresh_lock = self._refresh_locks[period]
        if cached and refresh_lock.locked():
            stale = cached if cached.stale else replace(cached, stale=True)
            self._cache[period] = stale
            return stale

        async with refresh_lock:
            cached = self._cache.get(period)
            if cached and now - cached.fetched_at < self._cache_ttl:
                return cached

            retry_after = self._retry_after.get(period)
            if retry_after and self._retry_clock() < retry_after:
                if cached:
                    return cached
                raise UpstreamUnavailableError("IGN earthquake data is unavailable")

            if cached and not cached.stale:
                cached = replace(cached, stale=True)
                self._cache[period] = cached

            try:
                content = await self._fetch_text()
                snapshot = EarthquakeSnapshot(
                    earthquakes=parse_ign_feed(content, collection=collection),
                    fetched_at=now,
                )
            except (UpstreamFetchError, IgnFeedParseError) as exc:
                self._retry_after[period] = (
                    self._retry_clock() + self._upstream_retry.total_seconds()
                )
                if cached:
                    return cached
                raise UpstreamUnavailableError("IGN earthquake data is unavailable") from exc

            self._cache[period] = snapshot
            self._retry_after.pop(period, None)
            return snapshot
