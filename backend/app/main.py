from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import Settings
from backend.app.services.earthquakes import (
    EarthquakeService,
    UpstreamFetchError,
    UpstreamUnavailableError,
)

SOURCE_NAME = "Instituto Geográfico Nacional (IGN)"


async def _fetch_ign_feed(
    settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None
) -> str:
    try:
        async with httpx.AsyncClient(
            timeout=settings.ign_timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": "Obratec-seismos/0.1 (+https://github.com/CabhuDev/Obratec-seismos)"},
            transport=transport,
        ) as client:
            async with client.stream("GET", settings.ign_feed_url) as response:
                response.raise_for_status()
                content = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(content) + len(chunk) > settings.ign_max_response_bytes:
                        raise UpstreamFetchError("IGN response limit exceeded")
                    content.extend(chunk)
                return content.decode(response.encoding or "utf-8")
    except (httpx.HTTPError, UnicodeError, LookupError) as exc:
        raise UpstreamFetchError("IGN feed request failed") from exc


def _build_service(settings: Settings) -> EarthquakeService:
    async def fetch_text() -> str:
        return await _fetch_ign_feed(settings)

    return EarthquakeService(
        fetch_text=fetch_text,
        cache_ttl=timedelta(seconds=settings.cache_ttl_seconds),
        upstream_retry=timedelta(seconds=settings.upstream_retry_seconds),
    )


def create_app(
    *,
    service: EarthquakeService | None = None,
    clock: Callable[[], datetime] | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings()
    earthquake_service = service or _build_service(resolved_settings)
    current_time = clock or (lambda: datetime.now(UTC))

    app = FastAPI(
        title="Obratec Seísmos API",
        version="0.1.0",
        description="Datos sísmicos de España procedentes del Instituto Geográfico Nacional.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/earthquakes")
    async def list_earthquakes(
        period: Literal["3d", "10d", "30d"] = "3d",
        min_magnitude: float = Query(default=0, ge=0, le=10),
        max_depth: float | None = Query(default=None, ge=0, le=1_000),
    ) -> dict[str, object]:
        try:
            snapshot = await earthquake_service.get_earthquakes(period, now=current_time())
        except UpstreamUnavailableError as exc:
            raise HTTPException(
                status_code=503,
                detail="Los datos del IGN no están disponibles temporalmente.",
            ) from exc

        items = [
            item
            for item in snapshot.earthquakes
            if float(item["magnitude"]) >= min_magnitude
            and (max_depth is None or float(item["depth_km"]) <= max_depth)
        ]
        items.sort(key=lambda item: str(item["occurred_at"]), reverse=True)

        fetched_at = snapshot.fetched_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
        return {
            "meta": {
                "count": len(items),
                "period": period,
                "stale": snapshot.stale,
                "fetched_at": fetched_at,
                "source": SOURCE_NAME,
            },
            "items": items,
        }

    return app


app = create_app()
