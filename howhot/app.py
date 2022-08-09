import os
import random
from datetime import datetime
from typing import Dict, List, Tuple

from flask import Flask, render_template
from flask_talisman import Talisman
from redis import from_url as get_redis_from_url

from howhot import EASTERN_TIMEZONE
from howhot.device_stats import get_battery_level
from howhot.shop_temp import get_shop_temp, get_shop_temperature_history
from howhot.weather import get_weather

app = Flask(__name__)


@app.route("/")
def render_index() -> str:
    redis = get_redis_from_url(os.environ["REDIS_URL"])
    weather = get_weather(redis)
    shop_temp = get_shop_temp(redis)
    battery_level = get_battery_level(redis)
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
    temp_history: Dict[str, Dict[str, int]]
) -> Tuple[List[str], List[str]]:
    years = set()
    dates = set()
    for key in temp_history.keys():
        month, day, year = key.split("-")
        years.add(year)
        dates.add(f"{month}-{day}")

    return sorted(list(years)), sorted(list(dates))


def format_data_for_chart(
    temp_history: Dict[str, Dict[str, int]]
) -> Tuple[List[str], Dict[str, List[int | None]]]:
    """
    Format the data for chart.js
    """
    years, dates = _get_years_and_dates(temp_history)
    datasets = {}
    for year in years:
        dataset: List[int | None] = []
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
    redis = get_redis_from_url(os.environ["REDIS_URL"])
    dates, datasets = format_data_for_chart(get_shop_temperature_history(redis))
    colors = {}
    for key in datasets:
        red, green, blue = random.choices(range(256), k=3)
        colors[key] = f"rgb({red}, {green}, {blue})"
    return render_template(
        "history.html", labels=dates, datasets=datasets, colors=colors
    )


@app.route("/history_raw")
def render_history_json() -> Dict[str, Dict[str, int]]:
    redis = get_redis_from_url(os.environ["REDIS_URL"])
    return get_shop_temperature_history(redis)


if __name__ == "__main__":
    Talisman(app)
    app.run(host="0.0.0.0")
