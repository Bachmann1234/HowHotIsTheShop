from datetime import datetime, UTC

import pytest
from fakeredis import FakeRedis

from howhot.shop_temp import ShopTemp, celsius_to_fahrenheit, get_shop_temp, heat_index


def test_get_shop_temp(fake_redis: FakeRedis) -> None:
    assert get_shop_temp(fake_redis) == ShopTemp(
        temperature=80,
        humidity=54,
        feels_like=81,
        time=datetime(2021, 7, 22, 1, 57, tzinfo=UTC),
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
