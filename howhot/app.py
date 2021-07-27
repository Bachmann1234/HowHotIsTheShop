import os
from datetime import datetime
from typing import Dict, Tuple, cast

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


def format_data_for_chart(
    temp_history: Dict[str, int]
) -> Tuple[Tuple[str], Tuple[int]]:
    """
    Format the data for chart.js
    """
    results = sorted(
        temp_history.items(),
        key=lambda k: datetime.strptime(k[0], "%m-%d-%Y"),
        reverse=False,
    )
    dates, temps = zip(*results)
    return cast(Tuple[str], dates), cast(Tuple[int], temps)


@app.route("/history")
def render_history() -> str:
    redis = get_redis_from_url(os.environ["REDIS_URL"])
    dates, temps = format_data_for_chart(get_shop_temperature_history(redis))
    return render_template("history.html", labels=dates, data=temps)


@app.route("/history_raw")
def render_history_json() -> str:
    redis = get_redis_from_url(os.environ["REDIS_URL"])
    return get_shop_temperature_history(redis)


if __name__ == "__main__":
    Talisman(app)
    app.run(host="0.0.0.0")
