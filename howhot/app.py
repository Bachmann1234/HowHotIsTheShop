import os
from datetime import datetime

from flask import Flask, render_template
from flask_talisman import Talisman
from redis import from_url as get_redis_from_url, Redis

from howhot import EASTERN_TIMEZONE
from howhot.shop_temp import get_shop_temp
from howhot.weather import get_weather

app = Flask(__name__)

_redis = None


def get_redis() -> Redis:
    global _redis
    if _redis:
        return _redis
    else:
        _redis = get_redis_from_url(os.environ.get("REDIS_URL"))
        return _redis


@app.route("/")
def render_temperature() -> str:
    weather = get_weather(get_redis())
    shop_temp = get_shop_temp()
    return render_template(
        "index.html",
        shop_temp=shop_temp,
        weather=weather,
        current_time=datetime.now()
        .astimezone(EASTERN_TIMEZONE)
        .strftime("%m-%d-%Y %H:%M:%S"),
    )


if __name__ == "__main__":
    Talisman(app)
    app.run(host="0.0.0.0")
