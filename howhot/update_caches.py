import os
import traceback

from redis import Redis
from redis import from_url as get_redis_from_url
from sendgrid import Mail, SendGridAPIClient

from howhot.device_stats import update_device_cache
from howhot.weather import update_weather_cache


def update_caches(redis: Redis) -> None:
    weather = update_weather_cache(
        redis=redis,
        lat=os.environ["WEATHER_LAT"],
        long=os.environ["WEATHER_LONG"],
        weather_api_key=os.environ["WEATHER_API_KEY"],
    )
    print("Updated Weather Cache!")
    print(weather)

    battery = update_device_cache(
        redis=redis,
        device_token=os.environ["GOVEE_DEVICE"],
        govee_email=os.environ["GOVEE_EMAIL"],
        govee_password=os.environ["GOVEE_PASSWORD"],
        govee_client=os.environ["GOVEE_CLIENT"],
    )
    print("Updated Battery Cache!")
    print(f"Battery Level {battery}")


def main(redis: Redis) -> None:
    try:
        update_caches(redis)
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


if __name__ == "__main__":
    main(get_redis_from_url(os.environ["REDIS_URL"]))
