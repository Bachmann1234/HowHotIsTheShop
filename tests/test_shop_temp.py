from howhot.shop_temp import ShopTemp, get_shop_temp


def test_get_shop_temp() -> None:
    assert get_shop_temp() == ShopTemp(
        temperature=26.72, humidity=53.68, time=1626919020000
    )
