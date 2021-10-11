import json
import os
import time
from typing import Dict, List, cast

import requests
from redis import Redis
from redis import from_url as get_redis_from_url

from howhot.device_stats import get_govee_auth_token
from howhot.shop_temp import (
    SHOP_HIGH_HISTORY_KEY,
    ShopTemp,
    update_max_history_from_point,
)


def backfill_history(
    redis: Redis,
    govee_sku: str,
    govee_device: str,
    govee_email: str,
    govee_password: str,
    govee_client: str,
) -> None:
    govee_token = get_govee_auth_token(govee_email, govee_password, govee_client, redis)
    task_ids = _request_backfill(govee_token, govee_sku, govee_device)
    data_links = []
    history: Dict[str, Dict[str, int]] = {}
    for task_id in task_ids:
        data_links += _get_data_links(task_id, govee_token)
    for data_link in data_links:
        print(f"Processing: {data_link}")
        _process_datafile(data_link, history)
    redis.set(SHOP_HIGH_HISTORY_KEY, json.dumps(history))


def _request_backfill(govee_token: str, govee_sku: str, govee_device: str) -> List[int]:
    response = requests.post(
        "https://app2.govee.com/th/v2/data-tasks",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {govee_token}",
        },
        json={
            "sku": govee_sku,
            "device": govee_device,
            "timeRange": {"start": -1, "end": int(time.time() * 1000)},
        },
    )

    response.raise_for_status()
    if response.json()["status"] != 200:
        raise ValueError("Failed to trigger task")
    return cast(List[int], response.json()["data"]["taskIds"])


def _get_data_links(task_id: int, govee_token: str) -> List[str]:
    while True:
        response = requests.get(
            f"https://app2.govee.com/th/v2/data-links?taskIds={task_id}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {govee_token}",
            },
        )

        response.raise_for_status()
        response_json = response.json()
        state = response_json["data"][0]["state"]
        if response_json["status"] != 200:
            raise ValueError("Failed to get task status")
        if state == 0:
            print(f"{task_id} is not done yet. Sleeping")
            time.sleep(5)
        elif state == 1:
            print(f"{task_id} complete. Sleeping")
            return cast(List[str], response.json()["data"][0]["links"])
        else:
            print(response.text)
            raise ValueError(f"Unknown task state {state}")


def _process_datafile(data_link: str, history: dict) -> None:
    response = requests.get(data_link)
    response.raise_for_status()
    for section in response.text.split(";"):
        for point in section.split("|"):
            temp, humidity, last_time = point.split(",")
            shop_temp = ShopTemp.from_params(temp, humidity, last_time)
            update_max_history_from_point(history, shop_temp)


if __name__ == "__main__":
    backfill_history(
        redis=get_redis_from_url(os.environ["REDIS_URL"]),
        govee_sku=os.environ["GOVEE_SKU"],
        govee_device=os.environ["GOVEE_DEVICE"],
        govee_email=os.environ["GOVEE_EMAIL"],
        govee_password=os.environ["GOVEE_PASSWORD"],
        govee_client=os.environ["GOVEE_CLIENT"],
    )
