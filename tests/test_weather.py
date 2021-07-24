from howhot.weather import Weather, get_weather


def test_get_weather() -> None:
    assert get_weather() == Weather(
        feels_like=66,
        humidity=75,
        temperature=66,
        description="clear sky",
        icon_code="01n",
    )
