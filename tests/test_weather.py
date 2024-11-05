import responses

from howhot.weather import Weather, get_weather, update_weather_cache
from tests.conftest import STUBBED_WEATHER_CALL


def test_get_weather() -> None:
    assert get_weather() == Weather(
        feels_like=66,
        humidity=75,
        temperature=66,
        description="clear sky",
        icon_code="01n",
    )


@responses.activate
def test_update_weather_cache() -> None:
    responses.add(
        responses.GET,
        "https://api.openweathermap.org/data/3.0/onecall"
        "?lat=-7.649245&lon=-113.5547542"
        "&exclude=minutely,hourly,"
        "daily,alerts&appid=fake_key&units=imperial",
        json=STUBBED_WEATHER_CALL,
        status=200,
    )

    assert update_weather_cache("-7.649245", "-113.5547542", "fake_key") == Weather(
        feels_like=66,
        humidity=75,
        temperature=66,
        description="clear sky",
        icon_code="01n",
    )
