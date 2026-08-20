from __future__ import annotations

import pytest

from backend.app.services.ign_parser import IgnFeedParseError, parse_ign_feed

SAMPLE_FEED = '''
var dias3 = {"type":"FeatureCollection","features":[
  {"type":"Feature","geometry":{"type":"Point","coordinates":[-3.6,37.1]},
   "properties":{"evid":"es2026test","mag":"2.4","magtype":"mbLg","depth":"10",
   "fecha":"2026-08-20 17:46:04","fechalocal":"2026-08-20 19:46:04",
   "loc":"SE CHURRIANA DE LA VEGA.GR","intensidad":"II"}}
]};
var dias10 = {"type":"FeatureCollection","features":[]};
'''


def test_parse_ign_feed_returns_normalized_earthquakes() -> None:
    earthquakes = parse_ign_feed(SAMPLE_FEED, collection="dias3")

    assert earthquakes == [
        {
            "id": "es2026test",
            "magnitude": 2.4,
            "magnitude_type": "mbLg",
            "depth_km": 10.0,
            "occurred_at": "2026-08-20T17:46:04Z",
            "local_time": "2026-08-20T19:46:04",
            "location": "SE CHURRIANA DE LA VEGA.GR",
            "intensity": "II",
            "longitude": -3.6,
            "latitude": 37.1,
        }
    ]


def test_parse_ign_feed_rejects_missing_collection() -> None:
    with pytest.raises(IgnFeedParseError, match="dias30"):
        parse_ign_feed(SAMPLE_FEED, collection="dias30")


@pytest.mark.parametrize(
    ("field", "original", "value"),
    [
        ("evid", '"es2026test"', '""'),
        ("evid", '"es2026test"', "null"),
        ("mag", '"2.4"', "NaN"),
        ("mag", '"2.4"', "Infinity"),
        ("depth", '"10"', '"-0.1"'),
    ],
)
def test_parse_ign_feed_rejects_invalid_properties(
    field: str, original: str, value: str
) -> None:
    content = SAMPLE_FEED.replace(f'"{field}":{original}', f'"{field}":{value}')

    with pytest.raises(IgnFeedParseError):
        parse_ign_feed(content, collection="dias3")


@pytest.mark.parametrize(
    "coordinates",
    ["[180.1,37.1]", "[-180.1,37.1]", "[-3.6,90.1]", "[-3.6,-90.1]"],
)
def test_parse_ign_feed_rejects_out_of_range_coordinates(coordinates: str) -> None:
    content = SAMPLE_FEED.replace("[-3.6,37.1]", coordinates)

    with pytest.raises(IgnFeedParseError, match="malformed"):
        parse_ign_feed(content, collection="dias3")
