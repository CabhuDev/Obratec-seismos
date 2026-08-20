from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from typing import Any


class IgnFeedParseError(ValueError):
    """Raised when the IGN feed cannot be parsed safely."""


def _reject_non_finite_json(value: str) -> None:
    raise ValueError(f"Non-finite JSON number: {value}")


def _utc_iso(value: str) -> str:
    parsed = datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    return parsed.isoformat().replace("+00:00", "Z")


def parse_ign_feed(content: str, *, collection: str) -> list[dict[str, object]]:
    if collection not in {"dias3", "dias10", "dias30"}:
        raise IgnFeedParseError(f"Unsupported collection: {collection}")

    match = re.search(
        rf"var\s+{re.escape(collection)}\s*=\s*(\{{.*?\}});",
        content,
        flags=re.DOTALL,
    )
    if not match:
        raise IgnFeedParseError(f"Collection {collection} was not found")

    try:
        payload: dict[str, Any] = json.loads(
            match.group(1), parse_constant=_reject_non_finite_json
        )
        features: list[dict[str, Any]] = payload["features"]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise IgnFeedParseError("The IGN feed has an invalid GeoJSON structure") from exc

    earthquakes: list[dict[str, object]] = []
    for feature in features:
        try:
            properties = feature["properties"]
            longitude, latitude = feature["geometry"]["coordinates"][:2]
            raw_earthquake_id = properties["evid"]
            if raw_earthquake_id is None:
                raise ValueError("Earthquake ID is empty")
            earthquake_id = str(raw_earthquake_id).strip()
            magnitude = float(properties["mag"])
            depth_km = float(properties["depth"])
            longitude = float(longitude)
            latitude = float(latitude)
            if (
                not earthquake_id
                or not all(
                    math.isfinite(value)
                    for value in (magnitude, depth_km, longitude, latitude)
                )
                or depth_km < 0
                or not -180 <= longitude <= 180
                or not -90 <= latitude <= 90
            ):
                raise ValueError("Earthquake values are outside their allowed ranges")

            earthquake = {
                "id": earthquake_id,
                "magnitude": magnitude,
                "magnitude_type": str(properties.get("magtype", "")).strip() or None,
                "depth_km": depth_km,
                "occurred_at": _utc_iso(str(properties["fecha"])),
                "local_time": (
                    str(properties.get("fechalocal", "")).strip().replace(" ", "T") or None
                ),
                "location": str(properties.get("loc", "")).strip(),
                "intensity": str(properties.get("intensidad", "")).strip() or None,
                "longitude": longitude,
                "latitude": latitude,
            }
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise IgnFeedParseError("An earthquake record is malformed") from exc
        earthquakes.append(earthquake)

    return earthquakes
