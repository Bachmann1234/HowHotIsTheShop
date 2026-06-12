from datetime import UTC, datetime

import pytest
import responses
from _pytest.monkeypatch import MonkeyPatch

from howhot import memory_cache
from howhot.device_stats import AUTH_KEY
from howhot.shop_temp import (
    SHOP_TEMP_KEY,
    ShopTemp,
    celsius_to_fahrenheit,
    get_shop_temp,
    heat_index,
)


def test_get_shop_temp() -> None:
    assert get_shop_temp() == ShopTemp(
        temperature=80,
        humidity=54,
        feels_like=81,
        time=datetime(2021, 7, 22, 1, 57, tzinfo=UTC),
    )


@responses.activate
def test_get_shop_temp_cold_cache(monkeypatch: MonkeyPatch) -> None:
    # An empty cache (e.g. right after a deploy) should trigger a device
    # update rather than erroring
    monkeypatch.setenv("GOVEE_DEVICE", "fakedevice")
    monkeypatch.setenv("GOVEE_EMAIL", "fakeEmail")
    monkeypatch.setenv("GOVEE_PASSWORD", "fakePass")
    monkeypatch.setenv("GOVEE_CLIENT", "fakeClient")
    memory_cache.clear_cache_entry(SHOP_TEMP_KEY)
    memory_cache.set_cache_value(AUTH_KEY, "fakeauthtoken")
    responses.add(
        responses.POST,
        "https://app2.govee.com/device/rest/devices/v1/list",
        json={
            "devices": [
                {
                    "device": "fakedevice",
                    "deviceExt": {
                        "deviceSettings": '{"battery":72}',
                        "lastDeviceData": '{"online":true,"tem":2559,"hum":5390,'
                        '"lastTime":1627185420000}',
                    },
                }
            ],
            "message": "",
            "status": 200,
        },
        status=200,
    )
    assert get_shop_temp() == ShopTemp(
        temperature=78,
        humidity=54,
        feels_like=78,
        time=datetime(2021, 7, 25, 3, 57, tzinfo=UTC),
    )


def test_celsius_to_fahrenheit() -> None:
    assert celsius_to_fahrenheit(0) == 32
    assert celsius_to_fahrenheit(-40) == -40
    assert celsius_to_fahrenheit(26.6667) == pytest.approx(80, 0.001)


def test_heat_index() -> None:
    assert heat_index(80, 75) == pytest.approx(83.575, 0.001)
    assert heat_index(80, 54) == pytest.approx(81.189, 0.001)
    # Simple formula gives 79.4, under the 80 threshold for the regression
    assert heat_index(81, 12) == pytest.approx(79.364, 0.001)
    assert heat_index(81, 85) == pytest.approx(87.425, 0.001)
    assert heat_index(70, 85) == pytest.approx(70.695, 0.001)
    # Muggy adjustment (RH > 85, 80-87F) is added, not subtracted
    assert heat_index(84, 88) == pytest.approx(97.366, 0.001)
