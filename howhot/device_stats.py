import json

import requests
from redis import Redis

DEVICE_KEY = "DEVICE_INFO"


def get_battery_level(redis: Redis) -> int:
    cached_devices_response = redis.get(DEVICE_KEY)
    assert cached_devices_response
    return int(cached_devices_response)


def update_battery_cache(redis: Redis, govee_token: str, device_token: str) -> int:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {govee_token}",
    }

    response = requests.post(
        "https://app2.govee.com/device/rest/devices/v1/list", headers=headers
    )

    response.raise_for_status()
    devices = response.json()["devices"]
    for device in devices:
        if device["device"] == device_token:
            settings = json.loads(device["deviceExt"]["deviceSettings"])
            battery = settings["battery"]
            redis.set(DEVICE_KEY, battery)
    battery_level = get_battery_level(redis)
    assert battery_level
    return battery_level
