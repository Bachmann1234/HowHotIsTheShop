from flask import Flask, render_template
from flask_talisman import Talisman

from howhot.shop_temp import get_shop_temp
from howhot.weather import get_weather

app = Flask(__name__)


@app.route("/")
def render_temperature() -> str:
    weather = get_weather()
    shop_temp = get_shop_temp()
    return render_template(
        "index.html", shop_temp=shop_temp.__dict__, wather=weather.__dict__
    )


if __name__ == "__main__":
    Talisman(app)
    app.run(host="0.0.0.0")
