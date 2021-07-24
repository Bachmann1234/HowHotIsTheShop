from dataclasses import dataclass


@dataclass
class Weather:
    feels_like: int
    humidity: int
    temperature: int
    description: str
    icon_code: str


def get_weather() -> Weather:
    cached_weather = _get_weather_from_cache()
    return Weather(
        feels_like=round(cached_weather["current"]["feels_like"]),
        humidity=round(cached_weather["current"]["humidity"]),
        temperature=round(cached_weather["current"]["temp"]),
        description=cached_weather["current"]["weather"][0]["description"],
        icon_code=cached_weather["current"]["weather"][0]["icon"],
    )


def _get_weather_from_cache() -> dict:
    return {
        "lat": 42.3826,
        "lon": -71.0772,
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
                {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01n"}
            ],
        },
    }
