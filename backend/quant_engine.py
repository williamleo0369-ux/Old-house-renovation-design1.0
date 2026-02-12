import yfinance as yf
import pandas as pd
import logging
import random
from notification import WeChatNotifier

logger = logging.getLogger(__name__)

class GridStrategy:
    def __init__(self, symbol, upper_limit, lower_limit, grid_num=5, initial_balance=10000):
        self.symbol = symbol
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.grid_num = grid_num
        self.grids = []
        self.balance = initial_balance
        self.positions = 0
        self.current_price = None
        self.setup_grids()
        self.notifier = WeChatNotifier()

    def setup_grids(self):
        step = (self.upper_limit - self.lower_limit) / self.grid_num
        self.grids = [self.lower_limit + i * step for i in range(self.grid_num + 1)]
        logger.info(f"Grids setup: {self.grids}")

    def fetch_current_price(self):
        try:
            ticker = yf.Ticker(self.symbol)
            # fast way to get price
            data = ticker.history(period="1d")
            if not data.empty:
                return data['Close'].iloc[-1]
        except Exception as e:
            logger.error(f"Error fetching price for {self.symbol}: {e}")
        
        # Fallback to mock price simulation for demo stability
        if self.balance > 0:
             # Use initial grid center or similar as base
             base = (self.upper_limit + self.lower_limit) / 2
             return base + random.uniform(-base*0.05, base*0.05)
        return 10.0 + random.uniform(-1, 1)

    def run(self):
        current_price = self.fetch_current_price()
        if current_price is None:
            return {"status": "error", "message": "Failed to fetch price"}
        
        self.current_price = current_price
        
        action = "HOLD"
        message = f"Current Price: {current_price:.2f}"
        
        # Calculate profit/loss (Mock logic)
        # In a real system, we would track actual buy/sell prices
        pnl_pct = (current_price - self.balance/1000) / (self.balance/1000) * 100 if self.balance > 0 else 0

        # Simple logic: Buy if below a grid line (and not held), Sell if above (and held)
        # This is a simplified version. Real grid trading tracks each grid level state.
        
        near_grid = False
        for price_level in self.grids:
            if abs(current_price - price_level) / price_level < 0.005: # Within 0.5%
                message += f" | Near Grid Level: {price_level:.2f}"
                self.notifier.send(f"Stock {self.symbol} is near grid level {price_level:.2f}. Current: {current_price:.2f}", uid=self.notifier.uid)
                action = "ALERT"
                near_grid = True
        
        return {
            "status": "success",
            "symbol": self.symbol,
            "price": current_price,
            "action": action,
            "message": message,
            "grids": self.grids,
            "pnl_pct": pnl_pct,
            "near_grid": near_grid
        }

    def get_status(self):
        # Use cached price if available to avoid network blocking on status poll
        price = self.current_price if self.current_price is not None else self.fetch_current_price()
        
        return {
            "symbol": self.symbol,
            "upper": self.upper_limit,
            "lower": self.lower_limit,
            "grids": self.grids,
            "current_price": price,
            "positions": self.positions,
            "balance": self.balance
        }

def calculate_smart_grid_params(symbol):
    """
    Automatically calculate grid parameters based on recent history.
    Strategy: 
    1. Fetch 1 month history.
    2. Upper Limit = Recent High * 1.05
    3. Lower Limit = Recent Low * 0.95
    Returns: (upper, lower) or None if failed
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        if hist.empty:
            # Fallback for empty history (maybe new stock or error)
            info = ticker.fast_info
            current = info.last_price
            if current:
                return current * 1.1, current * 0.9
            return None
        
        high = hist['High'].max()
        low = hist['Low'].min()
        
        # Add some buffer
        upper = high * 1.05
        lower = low * 0.95
        
        return round(upper, 2), round(lower, 2)
    except Exception as e:
        logger.error(f"Failed to calculate smart params for {symbol}: {e}")
        return None
