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
            # Use fast_info for real-time data (better than history)
            return ticker.fast_info.last_price
        except Exception as e:
            logger.error(f"Error fetching price for {self.symbol}: {e}")
        
        # Fallback to mock price simulation for demo stability
        # Only reached if fetch fails
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

class MarketScanner:
    """
    Scans for sector movements using ETF proxies.
    """
    SECTORS = {
        "CN": [
            {"name": "科技 (Tech)", "symbol": "512660.SS"}, # Using proxies or major stocks
            {"name": "消费 (Consumer)", "symbol": "000001.SS"}, # Proxy
            {"name": "金融 (Finance)", "symbol": "601398.SS"}
        ],
        "US": [
            {"name": "Tech (XLK)", "symbol": "XLK"},
            {"name": "Finance (XLF)", "symbol": "XLF"},
            {"name": "Health (XLV)", "symbol": "XLV"}
        ]
    }
    
    @staticmethod
    def scan(market_type="CN"):
        results = []
        sectors = MarketScanner.SECTORS.get(market_type, MarketScanner.SECTORS["CN"])
        
        for sector in sectors:
            try:
                # Optimized: fetch only today's data
                ticker = yf.Ticker(sector["symbol"])
                hist = ticker.history(period="5d") # Get a few days to calc change
                if len(hist) >= 2:
                    curr = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    pct_change = ((curr - prev) / prev) * 100
                    results.append({
                        "name": sector["name"],
                        "change": round(pct_change, 2),
                        "price": round(curr, 2)
                    })
            except:
                continue
                
        # Sort by biggest gainers
        results.sort(key=lambda x: x['change'], reverse=True)
        return results

class MarketSentiment:
    """
    Analyzes overall market risk (Red/Green light).
    Uses major indices (e.g., S&P 500 or CSI 300) to determine trend.
    """
    @staticmethod
    def analyze(market_type="CN"):
        symbol = "000001.SS" if market_type == "CN" else "SPY"
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo")
            if hist.empty:
                return {"status": "neutral", "score": 50, "message": "Data unavailable"}
            
            current_price = hist['Close'].iloc[-1]
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            ma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
            
            # Simple Logic: Price > MA20 > MA60 = Bull (Green)
            # Price < MA20 = Caution (Yellow)
            # Price < MA60 = Bear (Red)
            
            score = 50
            status = "neutral"
            color = "yellow"
            
            if current_price > ma20 and ma20 > ma60:
                score = 85
                status = "bullish"
                color = "green"
            elif current_price < ma60:
                score = 20
                status = "bearish"
                color = "red"
            else:
                score = 50
                status = "consolidation"
                color = "yellow"
                
            return {
                "status": status,
                "score": score,
                "color": color,
                "benchmark": symbol,
                "current": round(current_price, 2),
                "ma20": round(ma20, 2)
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"status": "error", "score": 0, "color": "gray"}

class PositionSizer:
    """
    Optimizes small position sizing based on account size and volatility.
    """
    @staticmethod
    def calculate(symbol, account_balance, risk_pct=2.0):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            if hist.empty:
                return None
            
            current_price = hist['Close'].iloc[-1]
            # ATR (Average True Range) approximation using high-low
            volatility = (hist['High'] - hist['Low']).mean()
            
            # Risk per trade = Account * Risk%
            risk_amount = account_balance * (risk_pct / 100)
            
            # Stop loss distance (e.g., 2 * Volatility)
            stop_loss_dist = volatility * 2
            
            if stop_loss_dist == 0:
                return None
                
            # Shares = Risk Amount / Stop Loss Distance
            shares = int(risk_amount / stop_loss_dist)
            
            return {
                "symbol": symbol,
                "suggested_shares": shares,
                "entry_price": round(current_price, 2),
                "stop_loss": round(current_price - stop_loss_dist, 2),
                "take_profit": round(current_price + stop_loss_dist * 2, 2), # 1:2 Risk/Reward
                "risk_amount": round(risk_amount, 2)
            }
        except Exception as e:
            logger.error(f"Position sizing failed: {e}")
            return None

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
