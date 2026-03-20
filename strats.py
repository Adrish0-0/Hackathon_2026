import logging 
import time
import yfinance as yf
from collections import deque
from basis import *


class RSICalculator:
    def __init__(self, period = 14):
        self.period = period
        
        self.prices = deque(maxlen = period * 3)
        self.average_gain = None
        self.average_loss = None
        self.previous_price = None
        self.current_rsi = None
        self.rsi_history = deque(maxlen = 50)
        
        self.update_count = 0
    
    
    def update(self, price):
        if self.previous_price is None:
            self.previous_price = price
            return None
        
        change = price - self.previous_price
        gain = max(change, 0)
        loss = abs(min(change, 0))
        
        self.prices.append(price)
        self.update_count += 1
        
        if len(self.prices) <= self.period:
            self.previous_price = price
            return None
        
        if self.average_gain is None:
            gains, losses = [], []
            prices_list = list(self.prices)
            
            for i in range(1, self.period + 1):
                changes = prices_list[i] - prices_list[i - 1]
                gains.append(max(changes, 0))
                losses.append(abs(min(changes, 0)))
            
            self.average_gain = sum(gains) / self.period
            self.average_loss = sum(losses) / self.period
        
        else:
            self.average_gain = ((self.average_gain * (self.period - 1)) + gain) / self.period
            self.average_loss = ((self.average_loss * (self.period - 1)) + loss) / self.period
        
        self.previous_price = price
        
        if self.average_loss == 0:
            self.current_rsi = 100.0
        else:
            rs = self.average_gain / self.average_loss
            self.current_rsi = 100 - (100 / (1 + rs))
        
        self.rsi_history.append(self.current_rsi)
        return self.current_rsi
    
    
    def get_rsi(self):
        return self.current_rsi
    
    
    def get_rsi_trend(self, lookback = 3):
        if len(self.rsi_history) < lookback:
            return "INSUFFICIENT_DATA"
        
        recent = list(self.rsi_history)[-lookback:]
        if recent[-1] > recent[0] * 1.02:
            return "RISING"
        elif recent[-1] < recent[0] * 0.98:
            return "FALLING"
        return "NEUTRAL"
    
    
    def is_divergence(self, price_trend):
        rsi_trend = self.get_rsi_trend()
        
        if price_trend == "DOWN" and rsi_trend == "RISING":
            return "BULLISH_DIVERGENCE"
        elif price_trend == "UP" and rsi_trend == "FALLING":
            return "BEARISH_DIVERGENCE"
        return None
    
    
    def get_statistics(self):
        return {
            "period": self.period,
            "updates": self.update_count,
            "current_rsi": self.current_rsi,
            "history_length": len(self.rsi_history),
            "is_warmed_up": self.current_rsi is not None
        }


class HistoryRSI:
    def __init__(self, coin):
        self.coin = coin
    
    
    def download_history(self, hours = 20):
        logging.info(f"Downloading {hours} hours of fresh historical data...")
        
        try:
            data = yf.download(
                f"{self.coin}-USD",
                period = "5d",
                interval = "1m", 
                progress = False
            )
            if data.empty:
                raise ValueError("No data returned from yfinance")
            
            closes = data["Close"].dropna().values
            
            prices = [float(price) for price in closes]
            
            if len(prices) >= hours:
                logging.info(f"Donwloaded {len(prices)} hours of data (using last {hours})")
                return prices[-hours:]
            else:
                logging.info(f"Downloaded {len(prices)} hours of data")
                return prices
        except Exception as e:
            logging.error(f"Failed to download history: {e}")
            logging.error(f"Bot will start without warmup")
            return []
    
    
    def warmup(self, rsi_calculator):
        logging.info("=" * 70)
        logging.info("RSI WARMUP - DOWNLOADING FRESH DATA")
        logging.info("=" * 70)
        
        prices = self.download_history()
        
        if len(prices) < 14:
            logging.error(f"Insufficient data: got {len(prices)} hours, need 14")
            return False
        
        logging.info(f"Calculating RSI from {len(prices)} historical prices...")
        
        valid_count = 0
        first_rsi_hour = None
        
        for i, price in enumerate(prices):
            rsi = rsi_calculator.update(price)
            if rsi is not None:
                valid_count += 1
                if first_rsi_hour is None:
                    first_rsi_hour = i + 1
                    logging.info(f"First valid RSI calculated at hour {first_rsi_hour}: {rsi:.2f}")
        
        final_rsi = rsi_calculator.get_rsi()
        
        logging.info(f"Warmup complete: {valid_count} RSI values calculated")
        logging.info(f"Starting RSI: {final_rsi:.2f}")
        logging.info("Ready to trade immediately!")
        logging.info("=" * 70)
        
        return True


class RSITradingStrategy:
    def __init__(self):
        self.rsi_calculator = RSICalculator()
        self.price_history = deque(maxlen = 50)
        
        self.position = 0
        self.entry_price = None
        
        self.consecutive_signals = 0
        self.last_signal_time = 0
        self.signal_history = []
        
        self.trades_today = 0
        self.daily_reset_time = time.time()
        self.total_pnl = 0.0
    
    
    def _get_price_trend(self, lookback = 3):
        if len(self.price_history) < lookback:
            return "NEUTRAL"
        recent = list(self.price_history)[-lookback:]
        change_pct = (recent[-1] - recent[0]) / recent[0]
        if change_pct > 0.02:
            return "UP"
        elif change_pct < -0.02:
            return "DOWN" 
        return "SIDEWAYS"
    
    
    def _get_dynamic_thresholds(self):
        trend = self._get_price_trend()
        if trend == "UP":
            return 75.0, 35.0
        elif trend == "DOWN":
            return 65.0, 25.0
        return 70.0, 30.0
    
    
    def _check_risk_limits(self, current_price):
        if self.position != 1 or self.entry_price is None:
            return None
        loss_pct = (self.entry_price - current_price) / self.entry_price
        if loss_pct >= 0.05:
            return "STOP_LOSS"
        profit_pct = (current_price - self.entry_price) / self.entry_price
        if profit_pct >= 0.1:
            return "TAKE_PROFIT"
        return None
    
    
    def _reset_daily_limits(self, current_time):
        if current_time - self.daily_reset_time > 86400:
            self.trades_today = 0
            self.daily_reset_time = current_time
    
    
    def generate_signal(self, price, current_time):
        self._reset_daily_limits(current_time)
        self.price_history.append(price)
        
        rsi = self.rsi_calculator.update(price)
        if rsi is None:
            return None, "RSI calculating...", None
        
        overbought, oversold = self._get_dynamic_thresholds()
        trend = self._get_price_trend()
        divergence = self.rsi_calculator.is_divergence(trend)
        
        status = (f"Price: ${price:,.2f} | RSI: {rsi:.1f} | Trend: {trend} | Position: {'LONG' if self.position else 'FLAT'}")
        logging.info(status)
        
        risk_signal = self._check_risk_limits(price)
        if risk_signal and self.position == 1:
            self.position = 0
            pnl = (price - self.entry_price) / self.entry_price * 100
            self.total_pnl += pnl
            return "SELL", f"{risk_signal} | P&L: {pnl:+.2f}%", rsi
        
        time_since_last = current_time - self.last_signal_time
        if time_since_last < 300:
            return None, f"Cooldown: {int(300 - time_since_last)}s", rsi
        if self.trades_today >= 10:
            return None, "Daily trade limit reached", rsi
        
        buy_conditions = []
        
        if rsi < oversold:
            buy_conditions.append(f"RSI oversold ({rsi:.1f})")
        
        if len(self.rsi_calculator.rsi_history) >= 2:
            prev_rsi = list(self.rsi_calculator.rsi_history)[-2]
            if prev_rsi < oversold and rsi >= oversold:
                buy_conditions.append("RSI crossed above oversold")
        
        if divergence == "BULLISH_DIVERGENCE":
            buy_conditions.append("Bullish divergence")
        
        if trend == "UP" and 45 < rsi < 55:
            buy_conditions.append("RSI support in uptrend")
        
        if buy_conditions and self.position == 0:
            self.consecutive_signals += 1
            if self.consecutive_signals >= 2:
                self.position = 1
                self.entry_price = price
                self.last_signal_time = current_time
                self.trades_today += 1
                self.consecutive_signals = 0
                return "BUY", " | ".join(buy_conditions), rsi
            return None, f"Buy confirmation {self.consecutive_signals}/2", rsi
        
        sell_conditions = []
        
        if rsi > overbought:
            sell_conditions.append(f"RSI overbought ({rsi:.1f})")
        
        if len(self.rsi_calculator.rsi_history) >= 2:
            prev_rsi = list(self.rsi_calculator.rsi_history)[-2]
            if prev_rsi > overbought and rsi <= overbought:
                sell_conditions.append("RSI crossed below overbought")
        
        if divergence == "BEARISH_DIVERGENCE":
            sell_conditions.append("Bearish divergence")
        
        if rsi > 85:
            sell_conditions.append(f"RSI extreme ({rsi:.1f})")
        
        if sell_conditions and self.position == 1:
            self.position = 0
            self.last_signal_time = current_time
            self.consecutive_signals = 0
            pnl = (price - self.entry_price) / self.entry_price * 100
            self.total_pnl += pnl
            return "SELL", f"{' | '.join(sell_conditions)} | P&L: {pnl:+.2f}%", rsi
        
        if not buy_conditions and not sell_conditions:
            self.consecutive_signals = 0
            
        return None, "No signal", rsi
    
    
    def get_status(self):
        return {
            "position": "LONG" if self.position else "FLAT",
            "entry_price": self.entry_price,
            "current_rsi": self.rsi_calculator.get_rsi(),
            "trades_today": self.trades_today,
            "total_pnl_pct": self.total_pnl,
            "total_trades": len(self.signal_history)
        }



class RSITradingBot:
    def __init__(self, coin, trade_quantity):
        self.coin = coin
        self.pair = f"{coin}/USD"
        self.trade_quantity = trade_quantity
        self.strategy = RSITradingStrategy()
        self.warmer = HistoryRSI(self.coin)
        self.running = False
        self.cycle_count = 0
        self.start_time = time.time()
        
        logging.info("=" * 70)
        logging.info("RSI TRADING BOT")
        logging.info("=" * 70)
        logging.info(f"Trading Pair: {self.coin}/USD")
        logging.info(f"Warmup: Downloads fresh 20h data every start")
        logging.info("=" * 70)
        
        self._warmup()
    
    
    def _warmup(self):
        success = self.warmer.warmup(self.strategy.rsi_calculator)
        if not success:
            logging.warning("Warmup failed - will calculate RSI from live data")
    
    
    def _execute_trade(self, side, price):
        order = place_order(self.coin, side, self.trade_quantity)
        if order:
            logging.info(f"{side} executed: {order}")
            return True
        else:
            logging.error(f"{side} failed")
            return False
    
    
    def run_cycle(self):
        self.cycle_count += 1
        current_time = time.time()
        
        response = get_ticker(self.pair)
        if response and "LastPrice" in response["Data"][self.pair]:
            price = float(response["Data"][self.pair]["LastPrice"])
        else:
            return
        
        signal, reason, rsi = self.strategy.generate_signal(price, current_time)
        if signal == "BUY":
            logging.info(f"BUY: {reason}")
            if not self._execute_trade("BUY", price):
                self.strategy.position = 0
        elif signal == "SELL":
            logging.info(f"SELL: {reason}")
            if not self._execute_trade("SELL", price):
                self.strategy.position = 1
        else:
            if self.cycle_count % 10 == 0:
                status = self.strategy.get_status()
                logging.info(f"Status: {status['position']} | RSI: {rsi:.1f} | P&L {status['total_pnl_pct']:+.2f}%")
    
    
    def run(self):
        self.running = True
        logging.info("Bot Started - Press Ctrl+C to stop")
        
        try:
            while self.running:
                self.run_cycle()
                time.sleep(60)
        except KeyboardInterrupt:
            logging.info("Shutdown requested")
            self.running = False
        finally:
            self._shutdown()
    
    
    def _shutdown(self):
        elapsed = time.time() - self.start_time
        status = self.strategy.get_status()
        
        logging.info("="*70)
        logging.info("SESSION COMPLETE")
        logging.info(f"Runtime: {elapsed/3600:.2f}h | Cycles: {self.cycle_count}")
        logging.info(f"Position: {status['position']} | P&L: {status['total_pnl_pct']:+.2f}%")
        if status['position'] == 'LONG':
            logging.warning("Position still open!")
        logging.info("=" * 70)
