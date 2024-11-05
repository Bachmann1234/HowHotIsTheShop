import json
import os
from dataclasses import dataclass

import requests

from howhot import memory_cache

WEATHER_CACHE_KEY = "CURRENT_WEATHER"


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


def get_weather() -> Weather:
    cached_weather_response = memory_cache.get_cache_value(WEATHER_CACHE_KEY)
    if not cached_weather_response:
        update_weather_cache(
            lat=os.environ["WEATHER_LAT"],
            long=os.environ["WEATHER_LONG"],
            weather_api_key=os.environ["WEATHER_API_KEY"],
        )
        cached_weather_response = memory_cache.get_cache_value(WEATHER_CACHE_KEY)
    return Weather.from_api_dict(json.loads(str(cached_weather_response)))


def update_weather_cache(lat: str, long: str, weather_api_key: str) -> Weather:
    weather = requests.get(
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={ lat }&lon={ long }"
        f"&exclude=minutely,hourly,"
        f"daily,alerts&appid={ weather_api_key }&units=imperial",
        timeout=10,
    )
    weather.raise_for_status()
    memory_cache.set_cache_value(WEATHER_CACHE_KEY, weather.text)
    return get_weather()
