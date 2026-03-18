import sys

from basis import *
from strategy import *


logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    handlers = [
        logging.FileHandler(f'bot_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


if __name__ == "__main__":
    bot = BuyLowSellHigh(
        coin = "FET",
        trade_quantity = 20,
        check_interval = 30
    )
    
    bot.run_continuously()
