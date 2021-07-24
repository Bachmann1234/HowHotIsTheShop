from dataclasses import dataclass
from datetime import datetime
from math import sqrt

from howhot import EASTERN_TIMEZONE


@dataclass
class ShopTemp:
    temperature: int  # F
    humidity: int  # Percent
    feels_like: int
    time: datetime  # Measurement Time

    def formatted_eastern_time(self):
        return self.time.astimezone(EASTERN_TIMEZONE).strftime("%m-%d-%Y %H:%M:%S")


def get_shop_temp() -> ShopTemp:
    cached_weather = _get_shop_weather_from_cache()
    temp_in_fahrenheit = celsius_to_fahrenheit(cached_weather["tem"] / 100)
    humidity = cached_weather["hum"] / 100
    return ShopTemp(
        temperature=round(temp_in_fahrenheit),
        humidity=round(humidity),
        feels_like=round(heat_index(temp_in_fahrenheit, humidity)),
        time=datetime.utcfromtimestamp(cached_weather["time"] / 1000),
    )


def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 1.8) + 32


def heat_index(fahrenheit_temp: float, relative_humidity: float) -> float:
    # https://www.weather.gov/media/epz/wxcalc/heatIndex.pdf
    # https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
    # Basically encoding the result of a linear regression

    result = 0.5 * (
        fahrenheit_temp
        + (61 + ((fahrenheit_temp - 68.0) * 1.2) + (relative_humidity * 0.094))
    )

    if (result + fahrenheit_temp) / 2 >= 80:
        result = (
            -42.379
            + 2.04901523 * fahrenheit_temp
            + 10.14333127 * relative_humidity
            - 0.22475541 * fahrenheit_temp * relative_humidity
            - 6.83783 * (10 ** -3) * (fahrenheit_temp ** 2)
            - 5.481717 * (10 ** -2) * (relative_humidity ** 2)
            + 1.22874 * (10 ** -3) * (fahrenheit_temp ** 2) * relative_humidity
            + 8.5282 * (10 ** -4) * fahrenheit_temp * (relative_humidity ** 2)
            - 1.99 * (10 ** -6) * (fahrenheit_temp ** 2) * (relative_humidity ** 2)
        )

        adjustment = 0.0
        if relative_humidity < 13 and 80 < fahrenheit_temp < 112:
            adjustment = ((13 - relative_humidity) / 4) * sqrt(
                (17 - abs(fahrenheit_temp - 95)) / 17
            )
        elif relative_humidity > 85 and 80 < fahrenheit_temp < 87:
            adjustment = ((relative_humidity - 85) / 10) * ((87 - fahrenheit_temp) / 5)
        result -= adjustment

    return result


def _get_shop_weather_from_cache() -> dict:
    return {"tem": 2672, "hum": 5368, "time": 1626919020000}
