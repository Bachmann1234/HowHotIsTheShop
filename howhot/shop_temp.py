import json
from dataclasses import dataclass
from datetime import datetime
from math import sqrt
from typing import Dict

import requests
from redis import Redis

from howhot import EASTERN_TIMEZONE

SHOP_HIGH_HISTORY_KEY = "SHOP_HIGH_HISTORY"
SHOP_TEMP_KEY = "SHOP_TEMP"
LAST_SHOP_MEASUREMENT_INDEX = "LAST_SHOP_MEASUREMENT_INDEX"

# Shop history is a dict whose key is the date (EST timezone, cuse the shop aint movin)
# to the maximum temperature observed that day
ShopHistory = Dict[str, float]


@dataclass
class ShopTemp:
    temperature: int  # F
    humidity: int  # Percent
    feels_like: int
    time: datetime  # Measurement Time

    @property
    def formatted_eastern_time(self):
        return self.time.astimezone(EASTERN_TIMEZONE).strftime("%m-%d-%Y %H:%M:%S")

    @property
    def formatted_eastern_date(self):
        return self.time.astimezone(EASTERN_TIMEZONE).strftime("%m-%d-%Y")

    @staticmethod
    def from_api_response(api_response: Dict) -> "ShopTemp":
        temp_in_fahrenheit = celsius_to_fahrenheit(api_response["tem"] / 100)
        humidity = api_response["hum"] / 100
        return ShopTemp(
            temperature=round(temp_in_fahrenheit),
            humidity=round(humidity),
            feels_like=round(heat_index(temp_in_fahrenheit, humidity)),
            time=datetime.utcfromtimestamp(api_response["time"] / 1000),
        )


def get_shop_temp(redis: Redis) -> ShopTemp:
    cached_shop_response = redis.get(SHOP_TEMP_KEY)
    assert cached_shop_response
    cached_shop_response = json.loads(cached_shop_response.decode("utf-8"))
    return ShopTemp.from_api_response(cached_shop_response)


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


def get_shop_temperature_history(redis: Redis) -> ShopHistory:
    shop_history = redis.get(SHOP_HIGH_HISTORY_KEY)
    return json.loads(shop_history.decode("utf-8")) if shop_history else {}


def update_shop_cache(
    redis: Redis,
    govee_token: str,
    govee_device: str,
    govee_sku: str,
) -> ShopTemp:
    last_index = redis.get(LAST_SHOP_MEASUREMENT_INDEX)
    last_index = int(last_index) if last_index else 0

    history = get_shop_temperature_history(redis)

    def get_page(index):
        payload = {
            "limit": 2880,
            "device": govee_device,
            "sku": govee_sku,
            "index": index,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {govee_token}",
        }

        response = requests.post(
            "https://app2.govee.com/th/rest/devices/v1/data/load",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    while True:
        print(f"Continuing from index {last_index}")
        response_dict = get_page(last_index)
        last_index = response_dict["index"]
        redis.set(LAST_SHOP_MEASUREMENT_INDEX, str(last_index))
        data = response_dict["datas"]
        if len(data):
            print(f"Found {len(data)} results!")
            most_recent_measurement = data[-1]
            redis.set(
                SHOP_TEMP_KEY, json.dumps(most_recent_measurement).encode("utf-8")
            )
            for d in data:
                shop_temp = ShopTemp.from_api_response(d)
                current_max = history.get(shop_temp.formatted_eastern_date, -100)
                if shop_temp.temperature > current_max:
                    history[shop_temp.formatted_eastern_date] = shop_temp.temperature
        else:
            redis.set(SHOP_HIGH_HISTORY_KEY, json.dumps(history))
            return get_shop_temp(redis)
