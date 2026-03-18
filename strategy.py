import logging
from datetime import datetime
from basis import *


class BuyLowSellHigh:
    def __init__(self, coin, trade_quantity, check_interval = 10):
        self.coin = coin
        self.pair = f"{coin}/USD"
        self.trade_quantity = trade_quantity
        self.check_interval = check_interval
        
        self.highest_price = 0
        self.lowest_price = float("inf")
        self.last_buy_price = None
        self.last_sell_price = None
        self.current_price = None
        self.position = 0
        self.trade_history = []
        
        self.buy_drop_percent = 0.002
        self.sell_rise_percent = 0.003
        self.stop_loss_percent = 0.005
        
        self.start_time = datetime.now()
        self.total_cycles = 0
        self.errors = 0
        
        logging.info(f"Bot initialized for {self.pair}")
    
    
    def get_current_price(self):
        try:
            response = get_ticker(self.pair)
            if response and "LastPrice" in response["Data"][self.pair]:
                price = float(response["Data"][self.pair]["LastPrice"])
                self.current_price = price
                return price
            return None
        except Exception as e:
            logging.error(f"[ERROR] Failed to get price: {e}")
            return None
    
    
    def update_prices_extremes(self, price):
        if price > self.highest_price:
            self.highest_price = price
            logging.info(f"New High: ${price:.4f}")
        if price < self.lowest_price:
            self.lowest_price = price
            logging.info(f"New Low: ${price:.4f}")
    
    
    def check_buy(self, price):
        if self.position != 0:
            return False
        if self.highest_price > 0:
            drop_percent = (self.highest_price - price) / self.highest_price
            if drop_percent >= self.buy_drop_percent:
                logging.info(f"BUY CHECKING: {drop_percent*100:.2f}% drop")
                return True
        return False
    
    
    def check_sell(self, price):
        if self.position != 1 or self.last_buy_price is None:
            return False
        loss_percent = (self.last_buy_price - price) / self.last_buy_price
        if loss_percent >= self.stop_loss_percent:
            logging.warning(f"STOP LOSS: {loss_percent*100:.2f}% loss")
            return True
        if self.lowest_price < float("inf"):
            rise_percent = (price - self.lowest_price) / self.lowest_price
            if rise_percent >= self.sell_rise_percent:
                logging.info(f"SELL CHECKING: {rise_percent*100:.2f}% rise")
                return True
        return False
    
    
    def execute_buy(self, price):
        logging.info(f"Executing BUY at ${price:.4f}")
        order = place_order(self.coin, "BUY", self.trade_quantity)
        if order:
            self.position = 1
            self.last_buy_price = price
            self.lowest_price = price
            self.trade_history.append({
                "time": datetime.now().isoformat(),
                "action": "BUY",
                "price": price
            })
            logging.info("BUY executed successfully")
            return True
        logging.error("BUY failed")
        return False
    
    
    def execute_sell(self, price):
        logging.info(f"Executing SELL at ${price:.4f}")
        order = place_order(self.coin, "SELL", self.trade_quantity)
        if order:
            profit = (price - self.last_buy_price) * self.trade_quantity
            self.position = 0
            self.last_sell_price = price
            self.highest_price = price
            self.trade_history.append({
                "time": datetime.now().isoformat(),
                "action": "SELL",
                "price": price,
                "profit": profit
            })
            logging.info(f"SELL executed, profit: ${profit:.4f}")
            return True
        logging.error("SELL failed")
        return False
    
    
    def log_status(self):
        uptime = datetime.now() - self.start_time
        logging.info(f"STATUS: Uptime = {uptime}, Cycles = {self.total_cycles}, Errors = {self.errors}, Position = {"HOLDING" if self.position else "EMPTY"}, Price = ${self.current_price or 0:.4f}")
    
    
    def run_cycle(self):
        try:
            price = self.get_current_price()
            if price is None:
                self.errors += 1
                return
            self.current_price = price
            self.total_cycles += 1
            self.update_prices_extremes(price)
            if self.check_buy(price):
                self.execute_buy(price)
            elif self.check_sell(price):
                self.execute_sell(price)
            
            if self.total_cycles % 10 == 0:
                self.log_status()
        except Exception as e:
            logging.error(f"Cycle error: {e}")
            self.errors += 1
    
    
    def run_continuously(self):
        logging.info("=" * 50)
        logging.info("STARTING TRADING BOT")
        logging.info("=" * 50)
        
        while True:
            self.run_cycle()
            time.sleep(self.check_interval)
