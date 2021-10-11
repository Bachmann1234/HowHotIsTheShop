import json

import requests
from redis import Redis

from howhot.shop_temp import SHOP_TEMP_KEY

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
            device_data = json.loads(device["deviceExt"]["lastDeviceData"])
            battery = settings["battery"]
            redis.set(DEVICE_KEY, battery)
            redis.set(SHOP_TEMP_KEY, json.dumps(device_data, indent=4).encode("utf-8"))
    battery_level = get_battery_level(redis)
    assert battery_level
    return battery_level
