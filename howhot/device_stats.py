import json
import os
import time

import requests

from howhot import memory_cache
from howhot.shop_temp import (
    SHOP_HIGH_HISTORY_KEY,
    SHOP_TEMP_KEY,
    ShopTemp,
    get_shop_temperature_history,
    update_max_history_from_point,
)

DEVICE_KEY = "DEVICE_INFO"
AUTH_KEY = "AUTH_KEY"


def update_device_cache(
    device_token: str,
    govee_email: str,
    govee_password: str,
    govee_client: str,
) -> int:
    govee_token = get_govee_auth_token(govee_email, govee_password, govee_client)

    response = requests.post(
        "https://app2.govee.com/device/rest/devices/v1/list",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {govee_token}",
        },
        timeout=30,
    )

    response.raise_for_status()
    history = get_shop_temperature_history()
    for device in response.json()["devices"]:
        if device["device"] == device_token:
            memory_cache.set_cache_value(
                DEVICE_KEY, json.loads(device["deviceExt"]["deviceSettings"])["battery"]
            )
            device_data = json.loads(device["deviceExt"]["lastDeviceData"])
            memory_cache.set_cache_value(SHOP_TEMP_KEY, json.dumps(device_data))
            shop_temp = ShopTemp.from_api_response(device_data)
            update_max_history_from_point(history, shop_temp)
            memory_cache.set_cache_value(SHOP_HIGH_HISTORY_KEY, json.dumps(history))
    battery_level = get_battery_level()
    return battery_level


def get_battery_level() -> int:
    cached_devices_response = memory_cache.get_cache_value(DEVICE_KEY)
    if not cached_devices_response:
        update_device_cache(
            device_token=os.environ["GOVEE_DEVICE"],
            govee_email=os.environ["GOVEE_EMAIL"],
            govee_password=os.environ["GOVEE_PASSWORD"],
            govee_client=os.environ["GOVEE_CLIENT"],
        )
        cached_devices_response = memory_cache.get_cache_value(DEVICE_KEY)
    assert cached_devices_response
    return int(cached_devices_response)


def get_govee_auth_token(
    govee_email: str, govee_password: str, govee_client: str
) -> str:
    cached_key = memory_cache.get_cache_value(AUTH_KEY)
    if cached_key:
        return cached_key
    response = requests.post(
        "https://app2.govee.com/account/rest/account/v1/login",
        headers={
            "Content-Type": "application/json",
        },
        json={
            "email": govee_email,
            "client": govee_client,
            "password": govee_password,
        },
        timeout=30,
    )

    response.raise_for_status()
    client_data = response.json()["client"]
    auth_key = client_data["token"]
    memory_cache.set_cache_value(
        AUTH_KEY, auth_key, time.time() + (client_data["tokenExpireCycle"] - 120)
    )
    return str(auth_key)
