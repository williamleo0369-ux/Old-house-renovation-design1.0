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
    try:
        t = yf.Ticker(sym)
        # Use fast_info for speed
        info = t.fast_info
        price = info.last_price
        prev_close = info.previous_close
        change = ((price - prev_close) / prev_close) * 100 if prev_close else 0
        
        return {
            "symbol": sym,
            "price": round(price, 2),
            "change_pct": round(change, 2)
        }
    except Exception:
        # Fallback if fetch fails
        seed = sum(ord(c) for c in sym)
        random.seed(seed)
        base = 100 + random.uniform(-50, 50)
        price = base + random.uniform(-2, 2)
        change = random.uniform(-2, 2)
        
        return {
            "symbol": sym, 
            "price": round(price, 2), 
            "change_pct": round(change, 2)
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
    with ThreadPoolExecutor(max_workers=10) as executor:
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
        # Map some common suffixes if needed or just pass through
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
             raise ValueError("Empty data returned")

        # Format for lightweight-charts
        # time, open, high, low, close
        data = []
        for index, row in hist.iterrows():
            data.append({
                "time": int(index.timestamp()), # UNIX timestamp for LW Charts
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close']
            })
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}. Falling back to mock data.")
        # Mock data generation
        import time
        import random
        data = []
        base_time = int(time.time()) - 30 * 24 * 3600
        price = 15.0
        for i in range(30):
            open_p = price
            close_p = price + random.uniform(-1, 1)
            high_p = max(open_p, close_p) + random.uniform(0, 0.5)
            low_p = min(open_p, close_p) - random.uniform(0, 0.5)
            data.append({
                "time": base_time + i * 24 * 3600,
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p
            })
            price = close_p
        return data

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
