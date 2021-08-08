from datetime import datetime, timedelta
from unittest.mock import patch

from howhot.check_temp_age import alert_if_shop_temp_old
from howhot.shop_temp import ShopTemp


def test_temp_too_old():
    with patch("howhot.check_temp_age.SendGridAPIClient") as sendgrid_mock:
        assert alert_if_shop_temp_old(
            ShopTemp(
                temperature=80,
                humidity=54,
                feels_like=81,
                time=datetime(2021, 8, 8, 1, 0),
            ),
            datetime(2021, 8, 8, 1, 0) + timedelta(hours=2),
        )
        sendgrid_mock.assert_called()
        assert len(sendgrid_mock.mock_calls) == 2
        send_call_mail_object = sendgrid_mock.mock_calls[1].args[0]
        assert (
            send_call_mail_object.personalizations[  # pylint: disable=protected-access
                0
            ]._tos[0]["name"]
            == "bachmann_personal"
        )
        assert send_call_mail_object.from_email.name == "bachmann_sendgrid"
        assert (
            send_call_mail_object.contents[0].content
            == "Thermometer has not updated in 2.00 hours"
        )


def test_temp_just_fine():
    with patch("howhot.check_temp_age.SendGridAPIClient") as sendgrid_mock:
        assert not alert_if_shop_temp_old(
            ShopTemp(
                temperature=80,
                humidity=54,
                feels_like=81,
                time=datetime(2021, 8, 8, 1, 0),
            ),
            datetime(2021, 8, 8, 1, 0) + timedelta(minutes=30),
        )
        sendgrid_mock.assert_not_called()


def test_temp_time_negative():
    with patch("howhot.check_temp_age.SendGridAPIClient") as sendgrid_mock:
        assert not alert_if_shop_temp_old(
            ShopTemp(
                temperature=80,
                humidity=54,
                feels_like=81,
                time=datetime(2021, 8, 8, 1, 0),
            ),
            datetime(2021, 8, 8, 1, 0) - timedelta(hours=2),
        )
        sendgrid_mock.assert_not_called()
