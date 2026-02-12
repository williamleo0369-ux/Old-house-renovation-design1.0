from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import os
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
from scheduler import start_scheduler, add_strategy, get_all_strategies_status
from quant_engine import calculate_smart_grid_params, MarketSentiment, PositionSizer, MarketScanner
from market_data import fetch_hybrid_data, calculate_atr, fetch_market_news
from report_generator import generate_report_image
from fastapi.responses import Response

app = FastAPI(title="Quant Analysis API")

# Simple In-Memory Cache
WATCHLIST_CACHE = {
    "timestamp": 0,
    "data": []
}
CACHE_DURATION = 30  # seconds

# Start Scheduler
start_scheduler()

# Watchlist Management
WATCHLIST_FILE = "watchlist.json"

def load_watchlist_file():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_watchlist_file(watchlist):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(watchlist, f)

class StrategyRequest(BaseModel):
    symbol: str
    upper: float
    lower: float
    uid: str

class WatchlistRequest(BaseModel):
    symbol: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

def fetch_stock_data(sym):
    # Use the new hybrid fetcher
    data = fetch_hybrid_data(sym)
    
    if data:
        return {
            "symbol": sym,
            "price": round(data["price"], 2),
            "change_pct": round(data["change_percent"], 2),
            "name": data.get("name", sym) # Pass name through
        }
    else:
        # Fallback if fetch fails (Simulated)
        seed = sum(ord(c) for c in sym)
        random.seed(seed)
        base = 100 + random.uniform(-50, 50)
        price = base + random.uniform(-2, 2)
        change = random.uniform(-2, 2)
        
        return {
            "symbol": sym, 
            "price": round(price, 2), 
            "change_pct": round(change, 2),
            "name": sym # Fallback name
        }

@app.get("/api/watchlist")
def get_watchlist():
    global WATCHLIST_CACHE
    
    # Check cache
    if time.time() - WATCHLIST_CACHE["timestamp"] < CACHE_DURATION:
        return WATCHLIST_CACHE["data"]

    symbols = load_watchlist_file()
    data = []
    
    # Parallel Fetching
    # Increased workers to 20 for faster I/O bound fetching
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(fetch_stock_data, symbols)
        data = list(results)
            
    # Update Cache
    WATCHLIST_CACHE["timestamp"] = time.time()
    WATCHLIST_CACHE["data"] = data
    
    return data

@app.post("/api/watchlist")
def add_to_watchlist(req: WatchlistRequest):
    current = load_watchlist_file()
    if req.symbol not in current:
        current.append(req.symbol)
        save_watchlist_file(current)
    
    # Auto-start strategy for the new symbol
    try:
        params = calculate_smart_grid_params(req.symbol)
        if params:
            upper, lower = params
            # Use a default UID or from env
            default_uid = os.environ.get("WX_UID", "default_user")
            add_strategy(req.symbol, upper, lower, default_uid)
            print(f"Auto-strategy started for {req.symbol}: {upper}-{lower}")
    except Exception as e:
        print(f"Failed to auto-start strategy for {req.symbol}: {e}")

    return {"status": "success", "watchlist": current}

@app.post("/api/watchlist/sync_strategies")
def sync_strategies():
    current = load_watchlist_file()
    started = []
    failed = []
    default_uid = os.environ.get("WX_UID", "default_user")
    
    for symbol in current:
        try:
            params = calculate_smart_grid_params(symbol)
            if params:
                upper, lower = params
                add_strategy(symbol, upper, lower, default_uid)
                started.append(symbol)
            else:
                failed.append(symbol)
        except Exception as e:
            print(f"Error syncing {symbol}: {e}")
            failed.append(symbol)
            
    return {"status": "success", "started": started, "failed": failed}

@app.delete("/api/watchlist/{symbol}")
def remove_from_watchlist(symbol: str):
    current = load_watchlist_file()
    if symbol in current:
        current.remove(symbol)
        save_watchlist_file(current)
    return {"status": "success", "watchlist": current}

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/kline")
def get_kline(symbol: str = "000001.SZ", period: str = "1mo", interval: str = "1d"):
    try:
        ticker = yf.Ticker(symbol)
        
        # Adjust period based on interval if not provided
        # 1m -> max 7d (usually 1d is enough for intraday view)
        if interval == "1m":
            period = "1d" # Intraday
        elif interval == "1h":
             period = "1mo"
        
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
             raise ValueError("Empty data returned")

        data = []
        for index, row in hist.iterrows():
            # For intraday (1m), LightweightCharts needs seconds.
            # For daily, it prefers YYYY-MM-DD string or timestamp.
            # Using timestamp is generally safe.
            data.append({
                "time": int(index.timestamp()), 
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
                "volume": row['Volume']
            })
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}. Falling back to mock data.")
        # ... existing mock logic ...
        return []

@app.get("/api/stock/details/{symbol}")
def get_stock_details(symbol: str):
    # Use the same hybrid fetcher for consistency
    data = fetch_hybrid_data(symbol)
    
    # Calculate ATR
    atr_data = calculate_atr(symbol)
    
    # Calculate Correlation (Simulated for now, can use beta from yfinance if needed)
    correlation = 0.85 # Placeholder, real calc is heavy.
    
    # Simulate Order Book (L1 -> L5)
    # If we had real L2, we would use it. 
    # Akshare doesn't provide L5 easily without login/paid APIs usually.
    current_price = data['price'] if data else 100.0
    
    # Generate fake depth around current price
    asks = []
    bids = []
    for i in range(1, 6):
        spread = 0.01 * i * (current_price / 1000) # tighter spread
        if spread < 0.01: spread = 0.01 * i
        
        asks.append({"price": current_price + spread, "volume": random.randint(100, 5000)})
        bids.append({"price": current_price - spread, "volume": random.randint(100, 5000)})
    
    asks.sort(key=lambda x: x['price']) # Lowest ask first
    bids.sort(key=lambda x: x['price'], reverse=True) # Highest bid first
    
    details = {
        "symbol": symbol,
        "name": data.get("name", symbol) if data else symbol,
        "price": current_price,
        "prev_close": data['prev_close'] if data else current_price,
        "volume": data['volume'] if data else 0,
        "currency": data['currency'] if data else 'CNY',
        "correlation": correlation,
        "atr": atr_data['atr'] if atr_data else None,
        "suggested_grid": atr_data['suggested_grid_width'] if atr_data else None,
        "order_book": {
            "asks": asks,
            "bids": bids
        }
    }
    return details

@app.post("/api/strategy/start")
def start_strategy_endpoint(req: StrategyRequest):
    try:
        sid = add_strategy(req.symbol, req.upper, req.lower, req.uid)
        return {"status": "success", "strategy_id": sid, "message": "Strategy started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies")
def get_strategies():
    return get_all_strategies_status()

@app.get("/api/market/sectors")
def get_market_sectors(type: str = "CN"):
    return MarketScanner.scan(type)

@app.get("/api/market/sentiment")
def get_market_sentiment(type: str = "CN"):
    return MarketSentiment.analyze(type)

@app.get("/api/analysis/position")
def get_position_sizing(symbol: str, balance: float = 10000.0):
    res = PositionSizer.calculate(symbol, balance)
    if not res:
        raise HTTPException(status_code=400, detail="Calculation failed")
    return res

@app.get("/api/market/news")
def get_news():
    """
    Get latest market news (Sci-Tech 50, Gold)
    """
    return fetch_market_news()

@app.get("/api/report/generate")
def generate_daily_report(symbol: str = "512100"):
    """
    Generates a daily report image and returns it as a downloadable file.
    """
    try:
        # Fetch latest data with fallback
        # Use fetch_stock_data which has built-in simulation fallback if API fails
        stock_info = fetch_stock_data(symbol)
        
        if not stock_info:
            # Should not happen due to fallback, but just in case
            raise HTTPException(status_code=404, detail="Symbol not found")
        
        close = stock_info['price']
        change = stock_info['change_pct']
        
        # Estimate OHLC for the report if we only have current price
        # (Since fetch_stock_data only returns price/change)
        # We simulate OHLC around the current price for visualization
        open_p = close / (1 + change/100)
        high = max(close, open_p) * 1.01
        low = min(close, open_p) * 0.99
        
        img_io = generate_report_image(
            symbol, 
            round(close, 2), 
            round(change, 2), 
            round(open_p, 2), 
            round(high, 2), 
            round(low, 2),
            name=stock_info.get("name", "")
        )
        
        return Response(content=img_io.getvalue(), media_type="image/png")
    except Exception as e:
        print(f"Report gen error: {e}")
        # Return a simple error image or text instead of 500?
        # For now, just raise 500 but at least we tried to use fallback data
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
