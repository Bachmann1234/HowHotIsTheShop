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
            "07-23-2021": 79,
            "07-24-2021": 80,
            "07-25-2021": 78,
            "07-26-2021": 85,
        }


def test_format_data() -> None:

    assert format_data_for_chart(
        {
            "07-23-2022": 79,
            "07-26-2021": 85,
            "07-24-2021": 80,
            "07-25-2021": 78,
            "07-23-2021": 79,
        }
    ) == (
        ("07-23-2021", "07-24-2021", "07-25-2021", "07-26-2021", "07-23-2022"),
        (79, 80, 78, 85, 79),
    )
