import hmac
import os
from datetime import datetime

from flask import Flask, render_template, request
from flask_compress import Compress
from werkzeug.exceptions import Forbidden

from howhot import EASTERN_TIMEZONE
from howhot.device_stats import get_battery_level
from howhot.shop_temp import get_shop_temp, get_shop_temperature_history
from howhot.update_caches import update_caches_with_alerts
from howhot.weather import get_weather

app = Flask(__name__)
Compress(app)

# Year-line palette, assigned by recency: the newest year always gets the
# clearest color on the dark theme, and it cycles if years outgrow it.
CHART_PALETTE = [
    "#e7ede9",
    "#3fc2b4",
    "#5a9fd6",
    "#a98fd6",
    "#e0a36b",
    "#7fcf9c",
    "#d68fb0",
    "#6fc7d6",
]


@app.route("/")
def render_index() -> str:
    weather = get_weather()
    shop_temp = get_shop_temp()
    battery_level = get_battery_level()
    return render_template(
        "index.html",
        shop_temp=shop_temp,
        weather=weather,
        battery_level=battery_level,
        current_time=datetime.now()
        .astimezone(EASTERN_TIMEZONE)
        .strftime("%m-%d-%Y %H:%M:%S"),
    )


def _get_years_and_dates(
    temp_history: dict[str, dict[str, int]],
) -> tuple[list[str], list[str]]:
    years = set()
    dates = set()
    for key in temp_history:
        month, day, year = key.split("-")
        years.add(year)
        dates.add(f"{month}-{day}")

    return sorted(list(years)), sorted(list(dates))


def format_data_for_chart(
    temp_history: dict[str, dict[str, int]],
) -> tuple[list[str], dict[str, list[int | None]]]:
    """
    Format the data for chart.js
    """
    years, dates = _get_years_and_dates(temp_history)
    datasets = {}
    for year in years:
        dataset: list[int | None] = []
        for date in dates:
            point = temp_history.get(f"{date}-{year}")
            if point:
                dataset.append(point["temp"])
            else:
                dataset.append(None)
        datasets[year] = dataset
    return dates, datasets


@app.route("/history")
def render_history() -> str:
    dates, datasets = format_data_for_chart(get_shop_temperature_history())
    colors = {
        year: CHART_PALETTE[index % len(CHART_PALETTE)]
        for index, year in enumerate(sorted(datasets, reverse=True))
    }
    current_year = datetime.now().astimezone(EASTERN_TIMEZONE).year
    default_years = {str(current_year), str(current_year - 1)} & datasets.keys()
    if not default_years and datasets:
        default_years = {max(datasets)}
    return render_template(
        "history.html",
        labels=dates,
        datasets=datasets,
        colors=colors,
        default_years=default_years,
    )


@app.route("/history_raw")
def render_history_json() -> dict[str, dict[str, int]]:
    return get_shop_temperature_history()


@app.route("/update", methods=["POST"])
def update() -> str:
    if not hmac.compare_digest(
        request.headers.get("api-key", ""), os.environ["API_KEY"]
    ):
        app.logger.warning("forbidden update request")
        raise Forbidden()
    update_caches_with_alerts()
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0")
