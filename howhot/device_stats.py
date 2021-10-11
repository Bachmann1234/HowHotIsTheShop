import json

import requests
from redis import Redis

from howhot.shop_temp import (
    SHOP_HIGH_HISTORY_KEY,
    SHOP_TEMP_KEY,
    ShopTemp,
    get_shop_temperature_history,
)

DEVICE_KEY = "DEVICE_INFO"
AUTH_KEY = "AUTH_KEY"


def get_battery_level(redis: Redis) -> int:
    cached_devices_response = redis.get(DEVICE_KEY)
    assert cached_devices_response
    return int(cached_devices_response)


def _get_auth_token(
    govee_email: str, govee_password: str, govee_client: str, redis: Redis
) -> str:
    auth_key = redis.get(AUTH_KEY)
    if auth_key:
        return str(auth_key.decode("utf-8"))
    headers = {
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://app2.govee.com/account/rest/account/v1/login",
        headers=headers,
        json={
            "email": govee_email,
            "client": govee_client,
            "password": govee_password,
        },
    )

    response.raise_for_status()
    client_data = response.json()["client"]
    auth_key = client_data["token"]
    redis.set(AUTH_KEY, auth_key, ex=int(client_data["tokenExpireCycle"]) - 120)
    return str(auth_key)


def update_device_cache(
    redis: Redis,
    device_token: str,
    govee_email: str,
    govee_password: str,
    govee_client: str,
) -> int:
    govee_token = _get_auth_token(govee_email, govee_password, govee_client, redis)

    response = requests.post(
        "https://app2.govee.com/device/rest/devices/v1/list",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {govee_token}",
        },
    )

    response.raise_for_status()
    history = get_shop_temperature_history(redis)
    for device in response.json()["devices"]:
        if device["device"] == device_token:
            device_data = json.loads(device["deviceExt"]["lastDeviceData"])
            redis.set(
                DEVICE_KEY, json.loads(device["deviceExt"]["deviceSettings"])["battery"]
            )
            redis.set(SHOP_TEMP_KEY, json.dumps(device_data, indent=4).encode("utf-8"))
            shop_temp = ShopTemp.from_api_response(device_data)
            current_max = history.get(shop_temp.formatted_eastern_date, -100)
            if shop_temp.temperature > current_max:
                history[shop_temp.formatted_eastern_date] = shop_temp.temperature
                redis.set(SHOP_HIGH_HISTORY_KEY, json.dumps(history))

    battery_level = get_battery_level(redis)
    assert battery_level
    return battery_level
