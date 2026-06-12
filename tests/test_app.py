import json

from howhot.app import (
    app,
    compute_normal_band,
    compute_year_stats,
    format_data_for_chart,
)


def test_index() -> None:
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200


def test_history() -> None:
    with app.test_client() as client:
        response = client.get("/history")
        assert response.status_code == 200
        # Fixture data is all from 2021. Neither the current nor previous
        # year is present, so the latest year falls back to visible
        body = response.data.decode("utf-8")
        assert body.count("hidden: false") == 1
        assert body.count("hidden: true") == 0


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


def test_compute_normal_band() -> None:
    dates = ["07-23", "07-24", "07-25"]
    datasets: dict[str, list[int | None]] = {
        "2021": [80, 84, None],
        "2022": [70, 90, 88],
        "2023": [75, None, 92],  # the highlight year is left out of the band
    }
    band = compute_normal_band(dates, datasets, "2023", window=0)
    assert band == {
        "lo": [70, 84, 88],
        "hi": [80, 90, 88],
        "mid": [75, 87, 88],
    }


def test_compute_normal_band_smooths_with_neighbors() -> None:
    datasets: dict[str, list[int | None]] = {
        "2021": [80, None, 90],
        "2022": [80, 84, 86],
    }
    band = compute_normal_band(["07-23", "07-24", "07-25"], datasets, "2022")
    # 2021 alone forms the band; the gap on 07-24 borrows its neighbors
    assert band["hi"] == [85, 85, 85]


def test_compute_year_stats() -> None:
    assert compute_year_stats(
        {
            "07-23-2022": {"temp": 86, "humidity": 48},
            "07-24-2022": {"temp": 91, "humidity": 41},
            # 07-25 missing: the gap breaks the streak
            "07-26-2022": {"temp": 88, "humidity": 44},
            "07-27-2022": {"temp": 70, "humidity": 50},
            "07-30-2021": {"temp": 84, "humidity": 60},
        }
    ) == [
        {
            "year": "2022",
            "logged": 4,
            "hot_days": 3,
            "scorchers": 1,
            "peak": 91,
            "peak_date": "Jul 24",
            "streak": 2,
        },
        {
            "year": "2021",
            "logged": 1,
            "hot_days": 0,
            "scorchers": 0,
            "peak": 84,
            "peak_date": "Jul 30",
            "streak": 0,
        },
    ]


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
        ["07-23", "07-24", "07-25", "07-26"],
        {"2021": [79, 80, 78, 85], "2022": [79, None, None, None]},
    )
