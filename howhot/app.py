import hmac
import os
from datetime import date, datetime

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
        for month_day in dates:
            point = temp_history.get(f"{month_day}-{year}")
            if point:
                dataset.append(point["temp"])
            else:
                dataset.append(None)
        datasets[year] = dataset
    return dates, datasets


WARM_DAY_F = 80
HOT_DAY_F = 85
SCORCHER_F = 90


def compute_normal_band(
    dates: list[str],
    datasets: dict[str, list[int | None]],
    highlight_year: str,
    window: int = 3,
) -> dict[str, list[int | None]]:
    """
    Collapse every year except highlight_year into a per-calendar-day
    min/max/mean, smoothed with a centered rolling mean so a single odd
    reading doesn't put a spike in the "normal" band.
    """
    other_years = [year for year in datasets if year != highlight_year]
    lo: list[float | None] = []
    hi: list[float | None] = []
    mid: list[float | None] = []
    for index in range(len(dates)):
        values = [
            value
            for year in other_years
            if (value := datasets[year][index]) is not None
        ]
        lo.append(min(values) if values else None)
        hi.append(max(values) if values else None)
        mid.append(sum(values) / len(values) if values else None)

    def smooth(series: list[float | None]) -> list[int | None]:
        smoothed: list[int | None] = []
        for index in range(len(series)):
            values = [
                value
                for value in series[max(0, index - window) : index + window + 1]
                if value is not None
            ]
            smoothed.append(round(sum(values) / len(values)) if values else None)
        return smoothed

    return {"lo": smooth(lo), "hi": smooth(hi), "mid": smooth(mid)}


def compute_year_stats(
    temp_history: dict[str, dict[str, int]],
) -> list[dict[str, int | str]]:
    """
    Per-year records for the "by year" table, newest year first. The streak
    counts consecutive logged calendar days at or above HOT_DAY_F, so gaps in
    the data break a streak rather than spanning it.
    """
    by_year: dict[str, list[tuple[date, int]]] = {}
    for key, point in temp_history.items():
        day = datetime.strptime(key, "%m-%d-%Y").date()
        by_year.setdefault(str(day.year), []).append((day, point["temp"]))

    stats: list[dict[str, int | str]] = []
    for year in sorted(by_year, reverse=True):
        days = sorted(by_year[year])
        peak_day, peak_temp = max(days, key=lambda entry: entry[1])
        best_streak = streak = 0
        previous_hot_day: date | None = None
        for day, temp in days:
            if temp >= HOT_DAY_F:
                in_a_row = (
                    previous_hot_day is not None and (day - previous_hot_day).days == 1
                )
                streak = streak + 1 if in_a_row else 1
                best_streak = max(best_streak, streak)
                previous_hot_day = day
        stats.append(
            {
                "year": year,
                "logged": len(days),
                "warm_days": sum(1 for _, temp in days if temp >= WARM_DAY_F),
                "hot_days": sum(1 for _, temp in days if temp >= HOT_DAY_F),
                "scorchers": sum(1 for _, temp in days if temp >= SCORCHER_F),
                "peak": peak_temp,
                "peak_date": f"{peak_day:%b} {peak_day.day}",
                "streak": best_streak,
            }
        )
    return stats


@app.route("/history")
def render_history() -> str:
    temp_history = get_shop_temperature_history()
    dates, datasets = format_data_for_chart(temp_history)
    colors = {
        year: CHART_PALETTE[index % len(CHART_PALETTE)]
        for index, year in enumerate(sorted(datasets, reverse=True))
    }
    current_year = datetime.now().astimezone(EASTERN_TIMEZONE).year
    default_years = {str(current_year), str(current_year - 1)} & datasets.keys()
    if not default_years and datasets:
        default_years = {max(datasets)}
    highlight_year = (
        str(current_year)
        if str(current_year) in datasets
        else max(datasets, default="")
    )
    band = (
        compute_normal_band(dates, datasets, highlight_year)
        if highlight_year
        else {"lo": [], "hi": [], "mid": []}
    )
    return render_template(
        "history.html",
        labels=dates,
        datasets=datasets,
        colors=colors,
        default_years=default_years,
        highlight_year=highlight_year,
        band=band,
        has_band=any(value is not None for value in band["hi"]),
        year_stats=compute_year_stats(temp_history),
        warm_day=WARM_DAY_F,
        hot_day=HOT_DAY_F,
        scorcher=SCORCHER_F,
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
