from dataclasses import dataclass
from datetime import datetime

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
        feels_like=round(feels_like_temp(temp_in_fahrenheit, humidity)),
        time=datetime.utcfromtimestamp(cached_weather["time"] / 1000),
    )


def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 1.8) + 32


def feels_like_temp(fahrenheit_temp: float, relative_humidity: float) -> float:
    # https://www.weather.gov/media/epz/wxcalc/heatIndex.pdf
    # Sure....
    """
    -42.379 + 2.04901523*F + 10.14333127*rh
                                       - 0.22475541*F*rh - 6.83783*Math.pow(10,-3)*F*F
                                       - 5.481717*Math.pow(10,-2)*rh*rh
                                       + 1.22874*Math.pow(10,-3)*F*F*rh
                                       + 8.5282*Math.pow(10,-4)*F*rh*rh
                                       - 1.99*Math.pow(10,-6)*F*F*rh*rh;
    """
    return (
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


def _get_shop_weather_from_cache() -> dict:
    return {"tem": 2672, "hum": 5368, "time": 1626919020000}
