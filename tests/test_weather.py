import json

import responses
from fakeredis import FakeRedis

from howhot.weather import WEATHER_REDIS_KEY, Weather, get_weather, update_weather_cache


def test_get_weather(stub_weather_api_response: dict) -> None:
    redis = FakeRedis()
    redis.set(WEATHER_REDIS_KEY, json.dumps(stub_weather_api_response).encode("utf-8"))
    assert get_weather(redis) == Weather(
        feels_like=66,
        humidity=75,
        temperature=66,
        description="clear sky",
        icon_code="01n",
    )


@responses.activate
def test_update_weather_cache(stub_weather_api_response: dict) -> None:
    redis = FakeRedis()
    responses.add(
        responses.GET,
        "https://api.openweathermap.org/data/2.5/onecall"
        "?lat=-7.649245&lon=-113.5547542"
        "&exclude=minutely,hourly,"
        "daily,alerts&appid=fake_key&units=imperial",
        json=stub_weather_api_response,
        status=200,
    )

    assert update_weather_cache(
        redis, "-7.649245", "-113.5547542", "fake_key"
    ) == Weather(
        feels_like=66,
        humidity=75,
        temperature=66,
        description="clear sky",
        icon_code="01n",
    )
