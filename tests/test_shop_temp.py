from datetime import datetime

import pytest

from howhot.shop_temp import (
    ShopTemp,
    celsius_to_fahrenheit,
    feels_like_temp,
    get_shop_temp,
)


def test_get_shop_temp() -> None:
    assert get_shop_temp() == ShopTemp(
        temperature=80,
        humidity=54,
        feels_like=81,
        time=datetime(2021, 7, 22, 1, 57),
    )


def test_celsius_to_fahrenheit() -> None:
    assert celsius_to_fahrenheit(0) == 32
    assert celsius_to_fahrenheit(-40) == -40
    assert celsius_to_fahrenheit(26.6667) == pytest.approx(80, 0.001)


def test_shop_feels_like() -> None:
    assert feels_like_temp(80, 75) == pytest.approx(83.575, 0.001)
