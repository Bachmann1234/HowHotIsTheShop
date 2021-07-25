import os

from redis import from_url as get_redis_from_url

from howhot.weather import update_weather_cache


def main():
    redis = get_redis_from_url(os.environ["REDIS_URL"])
    weather = update_weather_cache(
        redis,
        os.environ["WEATHER_LAT"],
        os.environ["WEATHER_LONG"],
        os.environ["WEATHER_API_KEY"],
    )
    print("Updated Weather Cache!")
    print(weather)


if __name__ == "__main__":
    main()
