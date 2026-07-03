import json
import logging
import os
import traceback
from datetime import datetime

from sendgrid import Mail, SendGridAPIClient

from howhot import EASTERN_TIMEZONE, memory_cache
from howhot.device_stats import update_device_cache
from howhot.shop_temp import (
    SHOP_HIGH_HISTORY_KEY,
    fill_missing_outside_temps,
    get_shop_temperature_history,
)
from howhot.weather import update_weather_cache

logger = logging.getLogger(__name__)


def update_caches() -> None:
    weather = update_weather_cache(
        lat=os.environ["WEATHER_LAT"],
        long=os.environ["WEATHER_LONG"],
        weather_api_key=os.environ["WEATHER_API_KEY"],
    )
    logger.info("Updated Weather Cache!")
    logger.info(weather)

    battery = update_device_cache(
        device_token=os.environ["GOVEE_DEVICE"],
        govee_email=os.environ["GOVEE_EMAIL"],
        govee_password=os.environ["GOVEE_PASSWORD"],
        govee_client=os.environ["GOVEE_CLIENT"],
    )
    logger.info("Updated Battery Cache!")
    logger.info("Battery Level %s", battery)

    # Backfill a few finalized days' outside highs each cycle. On a fresh
    # deploy this chews through history over a couple days; in steady state
    # only yesterday is ever missing.
    history = get_shop_temperature_history()
    filled = fill_missing_outside_temps(
        history,
        lat=os.environ["WEATHER_LAT"],
        long=os.environ["WEATHER_LONG"],
        weather_api_key=os.environ["WEATHER_API_KEY"],
        today=datetime.now().astimezone(EASTERN_TIMEZONE).date(),
        limit=3,
    )
    if filled:
        memory_cache.set_cache_value(SHOP_HIGH_HISTORY_KEY, json.dumps(history))
    logger.info("Filled %s outside temps", filled)


def update_caches_with_alerts() -> None:
    try:
        update_caches()
    except Exception:
        trace = traceback.format_exc()
        message = Mail(
            from_email=os.environ["SENDER"],
            to_emails=[os.environ["ADMIN_EMAIL"]],
            subject="Hot Hot Is The Shop Error",
            plain_text_content=trace,
        )
        SendGridAPIClient(os.environ["SENDGRID_API_KEY"]).send(message)
        raise


def main() -> None:
    update_caches_with_alerts()


if __name__ == "__main__":
    main()
