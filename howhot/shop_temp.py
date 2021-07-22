from dataclasses import dataclass


@dataclass
class ShopTemp:
    temperature: float  # F
    humidity: float  # Percent
    time: int  # Millisecond epoc utc


def get_shop_temp() -> ShopTemp:
    cached_temp = _get_shop_temp_from_cache()
    return ShopTemp(
        temperature=cached_temp["tem"] / 100,
        humidity=cached_temp["hum"] / 100,
        time=cached_temp["time"],
    )


def _get_shop_temp_from_cache() -> dict:
    return {"tem": 2672, "hum": 5368, "time": 1626919020000}
