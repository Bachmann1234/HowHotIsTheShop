import os
import traceback

from redis import Redis
from redis import from_url as get_redis_from_url
from sendgrid import Mail, SendGridAPIClient

from howhot.device_stats import update_battery_cache
from howhot.shop_temp import update_shop_cache
from howhot.weather import update_weather_cache


def _do_update(redis: Redis) -> None:
    weather = update_weather_cache(
        redis=redis,
        lat=os.environ["WEATHER_LAT"],
        long=os.environ["WEATHER_LONG"],
        weather_api_key=os.environ["WEATHER_API_KEY"],
    )
    print("Updated Weather Cache!")
    print(weather)

    shop_temp = update_shop_cache(
        redis=redis,
        govee_token=os.environ["GOVEE_TOKEN"],
        govee_device=os.environ["GOVEE_DEVICE"],
        govee_sku=os.environ["GOVEE_SKU"],
    )
    print("Updated Shop Cache!")
    print(shop_temp)

    battery = update_battery_cache(
        redis=redis,
        govee_token=os.environ["GOVEE_TOKEN"],
        device_token=os.environ["GOVEE_DEVICE"],
    )
    print("Updated Battery Cache!")
    print(f"Battery Level {battery}")


def main(redis: Redis) -> None:
    try:
        _do_update(redis)
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
