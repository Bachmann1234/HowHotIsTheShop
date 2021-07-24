import json

from fakeredis import FakeRedis

from howhot.weather import Weather, get_weather, WEATHER_REDIS_KEY


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
