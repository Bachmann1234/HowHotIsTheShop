import json

import pytest
from _pytest.monkeypatch import MonkeyPatch
from fakeredis import FakeRedis

from howhot import app
from howhot.weather import WEATHER_REDIS_KEY

# pylint: disable=redefined-outer-name


@pytest.fixture(autouse=True)
def setup_environment(
    monkeypatch: MonkeyPatch, stub_weather_api_response: dict
) -> None:
    redis = FakeRedis()
    redis.set(WEATHER_REDIS_KEY, json.dumps(stub_weather_api_response).encode("utf-8"))
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setattr(app, "get_redis_from_url", lambda _: redis)


@pytest.fixture
def stub_weather_api_response() -> dict:
    return {
        "lat": -7.649245,
        "lon": -113.5547542,
        "timezone": "America/New_York",
        "timezone_offset": -14400,
        "current": {
            "dt": 1626924976,
            "sunrise": 1626859566,
            "sunset": 1626912899,
            "temp": 66.27,
            "feels_like": 66.13,
            "pressure": 1012,
            "humidity": 75,
            "dew_point": 58.12,
            "uvi": 0,
            "clouds": 1,
            "visibility": 10000,
            "wind_speed": 8.99,
            "wind_deg": 323,
            "wind_gust": 11.99,
            "weather": [
                {
                    "id": 800,
                    "main": "Clear",
                    "description": "clear sky",
                    "icon": "01n",
                }
            ],
        },
    }
