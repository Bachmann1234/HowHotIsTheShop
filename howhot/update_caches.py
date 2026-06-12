import logging
import os
import traceback

from sendgrid import Mail, SendGridAPIClient

from howhot.device_stats import update_device_cache
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
