import json
from dataclasses import dataclass

import requests
from redis import Redis

WEATHER_REDIS_KEY = "CURRENT_WEATHER"


@dataclass
class Weather:
    feels_like: int
    humidity: int
    temperature: int
    description: str
    icon_code: str

    @staticmethod
    def from_api_dict(api_response: dict) -> "Weather":
        return Weather(
            feels_like=round(api_response["current"]["feels_like"]),
            humidity=round(api_response["current"]["humidity"]),
            temperature=round(api_response["current"]["temp"]),
            description=api_response["current"]["weather"][0]["description"],
            icon_code=api_response["current"]["weather"][0]["icon"],
        )


def get_weather(redis: Redis) -> Weather:
    cached_weather_response = redis.get(WEATHER_REDIS_KEY)
    assert cached_weather_response
    return Weather.from_api_dict(json.loads(cached_weather_response.decode("utf-8")))


def update_weather_cache(
    redis: Redis, lat: str, long: str, weather_api_key: str
) -> Weather:
    weather = requests.get(
        f"https://api.openweathermap.org/data/2.5/onecall"
        f"?lat={ lat }&lon={ long }"
        f"&exclude=minutely,hourly,"
        f"daily,alerts&appid={ weather_api_key }&units=imperial"
    )
    weather.raise_for_status()
    redis.set(WEATHER_REDIS_KEY, weather.text.encode("utf-8"))
    return get_weather(redis)
