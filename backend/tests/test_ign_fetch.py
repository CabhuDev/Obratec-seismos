from __future__ import annotations

import httpx
import pytest

from backend.app.config import Settings
from backend.app.main import _fetch_ign_feed
from backend.app.services.earthquakes import UpstreamFetchError


class TrackingStream(httpx.AsyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks
        self.emitted = 0

    async def __aiter__(self):
        for chunk in self.chunks:
            self.emitted += 1
            yield chunk


@pytest.mark.asyncio
async def test_fetch_stops_streaming_when_response_exceeds_limit() -> None:
    stream = TrackingStream([b"1234", b"56", b"must-not-be-read"])
    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=stream))
    settings = Settings(ign_max_response_bytes=5)

    with pytest.raises(UpstreamFetchError, match="response limit"):
        await _fetch_ign_feed(settings, transport=transport)

    assert stream.emitted == 2


@pytest.mark.asyncio
async def test_fetch_does_not_follow_redirects() -> None:
    requests: list[httpx.Request] = []

    def redirect(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(302, headers={"Location": "https://evil.example/feed"})

    with pytest.raises(UpstreamFetchError):
        await _fetch_ign_feed(Settings(), transport=httpx.MockTransport(redirect))

    assert len(requests) == 1