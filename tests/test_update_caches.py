from unittest.mock import Mock, call, patch

import pytest
from _pytest.monkeypatch import MonkeyPatch
from fakeredis import FakeRedis

from howhot import update_caches


def test_update_fail(monkeypatch: MonkeyPatch):
    # The happy path is uninteresting. Each function
    # is tested and the update path is called every
    # 10 minutes in production. But I do wanna at least
    # attempt to ensure failures call the email api properly
    monkeypatch.setenv("SENDER", "bachmann_sendgrid")
    monkeypatch.setenv("ADMIN_EMAIL", "bachmann_personal")
    monkeypatch.setenv("SENDGRID_API_KEY", "sendgrid_key")

    # So I did not send any other apis so updating should fail real quick
    with patch("howhot.update_caches.SendGridAPIClient") as sendgrid_mock:
        with pytest.raises(KeyError):
            update_caches.main(FakeRedis())
        assert sendgrid_mock.call_args_list == [call("sendgrid_key")]

        assert len(sendgrid_mock.mock_calls) == 2
        send_call_mail_object = sendgrid_mock.mock_calls[1].args[0]
        # I dont know what the hell is going on in the sendgrid library
        # And this is a likely weakness in the test.... but um...
        # I tested this live....
        assert (
            send_call_mail_object.personalizations[0]._tos[0]["name"]
            == "bachmann_personal"
        )
        assert send_call_mail_object.from_email.name == "bachmann_sendgrid"
        assert "KeyError" in send_call_mail_object.contents[0].content
        assert "update_caches.py" in send_call_mail_object.contents[0].content
        assert "main" in send_call_mail_object.contents[0].content
        assert "os.environ" in send_call_mail_object.contents[0].content
