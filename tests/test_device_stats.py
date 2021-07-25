import responses
from fakeredis import FakeRedis

from howhot.device_stats import get_battery_level, update_battery_cache


@responses.activate
def test_update_battery_cache() -> None:
    redis = FakeRedis()
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
    assert update_battery_cache(redis, "fakeToken", "fakedevice") == 72
    assert get_battery_level(redis) == 72
