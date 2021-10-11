import json

import pytest
from _pytest.monkeypatch import MonkeyPatch
from fakeredis import FakeRedis

from howhot import app
from howhot.device_stats import DEVICE_KEY
from howhot.shop_temp import SHOP_HIGH_HISTORY_KEY, SHOP_TEMP_KEY
from howhot.weather import WEATHER_REDIS_KEY

# pylint: disable=redefined-outer-name


@pytest.fixture(autouse=True)
def setup_environment(monkeypatch: MonkeyPatch, fake_redis: FakeRedis) -> None:
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setattr(app, "get_redis_from_url", lambda _: fake_redis)
    monkeypatch.setenv("SENDER", "bachmann_sendgrid")
    monkeypatch.setenv("ADMIN_EMAIL", "bachmann_personal")
    monkeypatch.setenv("SENDGRID_API_KEY", "sendgrid_key")


@pytest.fixture
def fake_redis(stub_weather_api_response: dict) -> FakeRedis:
    redis = FakeRedis()
    redis.set(WEATHER_REDIS_KEY, json.dumps(stub_weather_api_response).encode("utf-8"))
    redis.set(
        SHOP_TEMP_KEY,
        json.dumps({"tem": 2672, "hum": 5368, "lastTime": 1626919020000}).encode(
            "utf-8"
        ),
    )
    redis.set(
        SHOP_HIGH_HISTORY_KEY,
        json.dumps(
            {
                "07-23-2021": {"temp": 79, "humidity": 48},
                "07-24-2021": {"temp": 80, "humidity": 44},
                "07-25-2021": {"temp": 78, "humidity": 50},
                "07-26-2021": {"temp": 85, "humidity": 84},
            }
        ).encode("utf-8"),
    )
    redis.set(
        DEVICE_KEY,
        b"72",
    )
    return redis


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
