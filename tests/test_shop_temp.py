from datetime import UTC, date, datetime

import pytest
import responses
from _pytest.monkeypatch import MonkeyPatch

from howhot import memory_cache
from howhot.device_stats import AUTH_KEY
from howhot.shop_temp import (
    SHOP_TEMP_KEY,
    ShopTemp,
    celsius_to_fahrenheit,
    fill_missing_outside_temps,
    get_shop_temp,
    heat_index,
)


def _stub_day_summary(day: str, max_temp: float) -> None:
    responses.add(
        responses.GET,
        "https://api.openweathermap.org/data/3.0/onecall/day_summary"
        f"?lat=1&lon=2&date={day}&appid=key&units=imperial",
        json={"temperature": {"max": max_temp}},
        status=200,
    )


@responses.activate
def test_fill_missing_outside_temps() -> None:
    _stub_day_summary("2021-07-23", 70.4)
    _stub_day_summary("2021-07-24", 72.9)
    history = {
        "07-24-2021": {"temp": 80, "humidity": 44},
        "07-23-2021": {"temp": 79, "humidity": 48},
        # already has an outside high; must be left alone
        "07-25-2021": {"temp": 78, "humidity": 50, "outside_temp": 60},
        # today's high isn't final yet; must be skipped
        "07-26-2021": {"temp": 85, "humidity": 40},
    }

    filled = fill_missing_outside_temps(
        history, "1", "2", "key", today=date(2021, 7, 26)
    )

    assert filled == 2
    assert history["07-23-2021"]["outside_temp"] == 70
    assert history["07-24-2021"]["outside_temp"] == 73
    assert history["07-25-2021"]["outside_temp"] == 60
    assert "outside_temp" not in history["07-26-2021"]

    # Idempotent: nothing left to fill, so no further calls
    assert (
        fill_missing_outside_temps(history, "1", "2", "key", today=date(2021, 7, 26))
        == 0
    )


@responses.activate
def test_fill_missing_outside_temps_respects_limit_newest_first() -> None:
    _stub_day_summary("2021-07-24", 72.9)
    history = {
        "07-24-2021": {"temp": 80, "humidity": 44},
        "07-23-2021": {"temp": 79, "humidity": 48},
    }

    filled = fill_missing_outside_temps(
        history, "1", "2", "key", today=date(2021, 7, 26), limit=1
    )

    assert filled == 1
    # Newest pending day is filled first
    assert history["07-24-2021"]["outside_temp"] == 73
    assert "outside_temp" not in history["07-23-2021"]


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
