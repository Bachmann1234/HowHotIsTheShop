from datetime import datetime, UTC

import responses
from fakeredis import FakeRedis

from howhot import EASTERN_TIMEZONE
from howhot.device_stats import AUTH_KEY, get_battery_level, update_device_cache
from howhot.shop_temp import get_shop_temp, get_shop_temperature_history


@responses.activate
def test_update_battery_cache() -> None:
    redis = FakeRedis()
    responses.add(
        responses.POST,
        "https://app2.govee.com/account/rest/account/v1/login",
        json={
            "message": "Login successful",
            "status": 200,
            "client": {
                "A": "testiot.cert",
                "B": "testIot",
                "topic": "fake",
                "token": "fakeauthtoken",
                "refreshToken": "",
                "tokenExpireCycle": 57600,
                "client": "FAKE",
                "clientName": "Matt’s iPad",
                "accountId": "fake",
                "pushToken": "",
                "versionCode": "24",
                "versionName": "4.3.0",
                "sysVersion": "14.6",
                "isSavvyUser": False,
            },
        },
    )
    responses.add(
        responses.POST,
        "https://app2.govee.com/device/rest/devices/v1/list",
        json={
            "devices": [
                {
                    "device": "fakedevice",
                    "sku": "H5071",
                    "spec": "",
                    "versionHard": "1.03.00",
                    "versionSoft": "1.06.02",
                    "deviceName": "Wifi thermometer",
                    "deviceExt": {
                        "deviceSettings": '{"temMin":-2000,"temMax":6000,"temWarning":false,'
                        '"fahOpen":false,"temCali":0,"humMin":0,"humMax":10000,'
                        '"humWarning":false,"humCali":0,"netWaring":true,'
                        '"uploadRate":30,"battery":72,"wifiLevel":0,"bleName":'
                        '"Govee_name","address":"address","secretCode":"secret",'
                        '"sku":"H5071","device":"devicething","deviceName":'
                        '"Wifi thermometer","versionHard":"1.03.00",'
                        '"versionSoft":"1.06.02"}',
                        "lastDeviceData": '{"online":true,"tem":2559,"hum":5390,'
                        '"lastTime":1627185420000,"avgDayTem":2559,'
                        '"avgDayHum":5390}',
                        "extResources": '{"skuUrl":"https://d1f2504ijhdyjw.cloudfront.net/sku-img'
                        "/f8f5045355d933ef5d66ca39b3d43e06-"
                        'add_list_type_device_5071.png","headOnImg":"",'
                        '"headOffImg":"","ext":"","ic":0}',
                    },
                    "goodsType": 0,
                }
            ],
            "message": "",
            "status": 200,
        },
        status=200,
    )
    assert (
        update_device_cache(redis, "fakedevice", "fakeEmail", "fakePass", "fakeClient")
        == 72
    )
    api_date = (
        datetime.fromtimestamp(1627185420000 / 1000, UTC)
        .astimezone(EASTERN_TIMEZONE)
        .strftime("%m-%d-%Y")
    )
    assert get_battery_level(redis) == 72
    assert get_shop_temp(redis).temperature == 78
    assert redis.get(AUTH_KEY) == b"fakeauthtoken"
    history = get_shop_temperature_history(redis)
    assert history[api_date] == {"humidity": 54, "temp": 78}

    # Now read a colder temp and ensure that history does not update
    # Also clearing responses verifies we use the cached auth token
    responses.reset()
    responses.add(
        responses.POST,
        "https://app2.govee.com/device/rest/devices/v1/list",
        json={
            "devices": [
                {
                    "device": "fakedevice",
                    "sku": "H5071",
                    "spec": "",
                    "versionHard": "1.03.00",
                    "versionSoft": "1.06.02",
                    "deviceName": "Wifi thermometer",
                    "deviceExt": {
                        "deviceSettings": '{"temMin":-2000,"temMax":6000,"temWarning":false,'
                        '"fahOpen":false,"temCali":0,"humMin":0,"humMax":10000,'
                        '"humWarning":false,"humCali":0,"netWaring":true,'
                        '"uploadRate":30,"battery":72,"wifiLevel":0,"bleName":'
                        '"Govee_name","address":"address","secretCode":"secret",'
                        '"sku":"H5071","device":"devicething","deviceName":'
                        '"Wifi thermometer","versionHard":"1.03.00",'
                        '"versionSoft":"1.06.02"}',
                        "lastDeviceData": '{"online":true,"tem":1559,"hum":4390,'
                        '"lastTime":1627185420000,"avgDayTem":1559,'
                        '"avgDayHum":4390}',
                        "extResources": '{"skuUrl":"https://d1f2504ijhdyjw.cloudfront.net/sku-img'
                        "/f8f5045355d933ef5d66ca39b3d43e06-"
                        'add_list_type_device_5071.png","headOnImg":"",'
                        '"headOffImg":"","ext":"","ic":0}',
                    },
                    "goodsType": 0,
                }
            ],
            "message": "",
            "status": 200,
        },
        status=200,
    )
    update_device_cache(redis, "fakedevice", "fakeEmail", "fakePass", "fakeClient")
    history = get_shop_temperature_history(redis)
    assert history[api_date] == {"humidity": 54, "temp": 78}
