import os
from datetime import datetime

from sendgrid import Mail, SendGridAPIClient

from howhot.shop_temp import ShopTemp, get_shop_temp

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = 60 * SECONDS_IN_MINUTE
TEMP_TOO_OLD = SECONDS_IN_HOUR * 1.5


def alert_if_shop_temp_old(shop_temp: ShopTemp, current_time: datetime) -> bool:
    time_diff = current_time - shop_temp.time
    temp_too_old = time_diff.total_seconds() > TEMP_TOO_OLD
    if temp_too_old:
        message = Mail(
            from_email=os.environ["SENDER"],
            to_emails=[os.environ["ADMIN_EMAIL"]],
            subject="Hot Hot Is The Shop Thermometer Disconnected",
            plain_text_content=f"Thermometer has not updated in"
            f" {time_diff.total_seconds()/60/60:.2f} hours",
        )
        SendGridAPIClient(os.environ["SENDGRID_API_KEY"]).send(message)
    return temp_too_old


def main() -> None:
    current_time = datetime.now()
    shop_temp = get_shop_temp()
    too_old = alert_if_shop_temp_old(shop_temp, current_time)
    if too_old:
        print("Thermometer has not updated in a while")
    else:
        print("Thermometer is updating just fine")


if __name__ == "__main__":
    main()
