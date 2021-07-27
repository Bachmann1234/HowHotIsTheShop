from datetime import datetime

import pytest
import responses
from fakeredis import FakeRedis

from howhot.shop_temp import (
    LAST_SHOP_MEASUREMENT_INDEX,
    ShopTemp,
    celsius_to_fahrenheit,
    get_shop_temp,
    heat_index,
    update_shop_cache,
)


def test_get_shop_temp(fake_redis: FakeRedis) -> None:
    assert get_shop_temp(fake_redis) == ShopTemp(
        temperature=80,
        humidity=54,
        feels_like=81,
        time=datetime(2021, 7, 22, 1, 57),
    )


def test_celsius_to_fahrenheit() -> None:
    assert celsius_to_fahrenheit(0) == 32
    assert celsius_to_fahrenheit(-40) == -40
    assert celsius_to_fahrenheit(26.6667) == pytest.approx(80, 0.001)


def test_heat_index() -> None:
    assert heat_index(80, 75) == pytest.approx(83.575, 0.001)
    assert heat_index(80, 54) == pytest.approx(81.189, 0.001)
    assert heat_index(81, 12) == pytest.approx(78.795, 0.001)
    assert heat_index(81, 85) == pytest.approx(87.425, 0.001)
    assert heat_index(70, 85) == pytest.approx(70.695, 0.001)
    assert heat_index(84, 88) == pytest.approx(97.005, 0.001)


@responses.activate
def test_update_shop_cache() -> None:
    redis = FakeRedis()
    responses.add(
        responses.POST,
        url="https://app2.govee.com/th/rest/devices/v1/data/load",
        json={
            "datas": [
                {"tem": 2474, "hum": 7116, "time": 1625090780000},
                {"tem": 2377, "hum": 7116, "time": 1625190770000},
                {"tem": 2374, "hum": 7116, "time": 1625190780000},
            ],
            "index": 2954762,
            "message": "",
            "status": 200,
        },
        match=[
            responses.json_params_matcher(
                {  # type: ignore
                    "limit": 2880,  # type: ignore
                    "device": "fakedevice",  # type: ignore
                    "sku": "fakesku",  # type: ignore
                    "index": 0,  # type: ignore
                }
            )
        ],
    )
    responses.add(
        responses.POST,
        url="https://app2.govee.com/th/rest/devices/v1/data/load",
        json={"datas": [], "index": 3016603, "message": "", "status": 200},
        match=[
            responses.json_params_matcher(
                {  # type: ignore
                    "limit": 2880,  # type: ignore
                    "device": "fakedevice",  # type: ignore
                    "sku": "fakesku",  # type: ignore
                    "index": 2954762,  # type: ignore
                }
            )
        ],
    )

    result = update_shop_cache(redis, "fakeToken", "fakedevice", "fakesku")

    assert redis.get(LAST_SHOP_MEASUREMENT_INDEX) == b"3016603"
    assert redis.get("SHOP_HIGH_HISTORY") == b'{"06-30-2021": 77, "07-02-2021": 75}'
    assert result == ShopTemp(
        temperature=75,
        humidity=71,
        feels_like=75,
        time=datetime(2021, 7, 2, 1, 53),
    )
