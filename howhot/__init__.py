import logging
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

EASTERN_TIMEZONE = ZoneInfo("America/New_York")
