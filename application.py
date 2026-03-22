import sys
import logging
from datetime import datetime
from basis import *
from strats import *


logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    handlers = [
        logging.FileHandler(f'bot_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


if __name__ == "__main__":
    bot = RSITradingBot(
        coin = "BTC",
        trade_quantity = 0.5,
    )
    
    bot.run()
