import json

from howhot.app import app, format_data_for_chart


def test_index() -> None:
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200


def test_history() -> None:
    with app.test_client() as client:
        response = client.get("/history")
        assert response.status_code == 200


def test_history_raw() -> None:
    with app.test_client() as client:
        response = client.get("/history_raw")
        assert response.status_code == 200
        assert json.loads(response.data.decode("utf-8")) == {
            "07-23-2021": {"humidity": 48, "temp": 79},
            "07-24-2021": {"humidity": 44, "temp": 80},
            "07-25-2021": {"humidity": 50, "temp": 78},
            "07-26-2021": {"humidity": 84, "temp": 85},
        }


def test_format_data() -> None:

    assert format_data_for_chart(
        {
            "07-23-2022": {"temp": 79, "humidity": 48},
            "07-26-2021": {"temp": 85, "humidity": 10},
            "07-24-2021": {"temp": 80, "humidity": 30},
            "07-25-2021": {"temp": 78, "humidity": 50},
            "07-23-2021": {"temp": 79, "humidity": 80},
        }
    ) == (
        ("07-23-2021", "07-24-2021", "07-25-2021", "07-26-2021", "07-23-2022"),
        [79, 80, 78, 85, 79],
        [80, 30, 50, 10, 48],
    )
