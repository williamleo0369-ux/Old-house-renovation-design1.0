
import akshare as ak
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures
import time

# Cache for ETF list to avoid frequent heavy API calls
ETF_LIST_CACHE = {
    "data": None,
    "timestamp": 0
}

# Cache for stock list
STOCK_LIST_CACHE = {
    "data": None,
    "timestamp": 0
}

# Cache for News
NEWS_CACHE = {
    "data": [],
    "timestamp": 0
}

def fetch_market_news(keywords=["科创50", "黄金"]):
    """
    Fetches market news and filters by keywords.
    Uses Akshare's generic news or a simple scraper if Akshare is too heavy/limited.
    For simplicity and reliability, we will mock this or use a simple RSS/API if available.
    Akshare's stock_news_em is good but might be heavy.
    
    Let's use a simulated news fetcher for stability in this demo environment,
    or try to fetch real headlines if possible.
    """
    global NEWS_CACHE
    # Update every 30 mins (1800s)
    if time.time() - NEWS_CACHE["timestamp"] < 1800 and NEWS_CACHE["data"]:
        return NEWS_CACHE["data"]
        
    news_items = []
    
    try:
        # Try fetching from EastMoney Main News via Akshare
        # stock_info_global_cls usually gives 7x24 global news
        # Columns: ['标题', '内容', '发布日期', '发布时间']
        df = ak.stock_info_global_cls(symbol="全部")
        
        for _, row in df.iterrows():
            title = str(row['标题']) if row['标题'] else ""
            content = str(row['内容'])
            # Combine title and content for keyword search
            text = f"{title} {content}".strip()
            
            # Filter by keywords
            matched = False
            matched_kw = ""
            for kw in keywords:
                if kw in text:
                    matched = True
                    matched_kw = kw
                    break
            
            if matched:
                # Determine Sentiment (Simple Heuristic)
                sentiment = "neutral"
                if any(x in text for x in ["涨", "利好", "突破", "新高", "买入", "增持", "预增"]):
                    sentiment = "positive"
                elif any(x in text for x in ["跌", "利空", "破位", "新低", "卖出", "减持", "预减"]):
                    sentiment = "negative"
                
                # Format time
                time_val = row['发布时间']
                time_str = time_val.strftime("%H:%M") if hasattr(time_val, 'strftime') else str(time_val)

                # Use content if title is empty
                display_text = title if title else content
                if len(display_text) > 60:
                    display_text = display_text[:60] + "..."

                news_items.append({
                    "time": time_str,
                    "content": display_text,
                    "sentiment": sentiment,
                    "keyword": matched_kw
                })
        
        # If no news found matching keywords, add generic market news or mock
        if not news_items:
             current_time = datetime.now().strftime("%H:%M")
             news_items = [
                 {"time": current_time, "content": "暂无关于'科创50'或'黄金'的最新快讯，市场情绪平稳。", "sentiment": "neutral"}
             ]
             
        NEWS_CACHE["data"] = news_items[:10] # Keep top 10
        NEWS_CACHE["timestamp"] = time.time()
        
    except Exception as e:
        print(f"News fetch error: {e}")
        # Fallback Mock
        current_time = datetime.now().strftime("%H:%M")
        NEWS_CACHE["data"] = [
             {"time": current_time, "content": "系统消息: 新闻服务暂时不可用 (API Error)", "sentiment": "neutral"}
        ]
        
    return NEWS_CACHE["data"]


CACHE_DURATION = 3600  # 1 hour

def get_etf_realtime_price(symbol: str):
    """
    Get real-time price for ETF using akshare (East Money source).
    Symbol should be 6 digits (e.g., '510300').
    """
    global ETF_LIST_CACHE
    
    try:
        # Check cache first
        if ETF_LIST_CACHE["data"] is not None and time.time() - ETF_LIST_CACHE["timestamp"] < 60:
            # Short cache for price lookup optimization if we just fetched it
            df = ETF_LIST_CACHE["data"]
        else:
            # Fetch all ETF spot data
            # This returns a DataFrame with all ETFs. It's heavy but comprehensive.
            df = ak.fund_etf_spot_em()
            ETF_LIST_CACHE["data"] = df
            ETF_LIST_CACHE["timestamp"] = time.time()
        
        # Filter for the symbol
        # Columns usually include: 代码, 名称, 最新价, 涨跌幅, ...
        # '代码' column is string.
        row = df[df['代码'] == symbol]
        
        if not row.empty:
            price = float(row.iloc[0]['最新价'])
            change_percent = float(row.iloc[0]['涨跌幅'])
            name = row.iloc[0]['名称']
            prev_close = price / (1 + change_percent/100) # Estimate prev close
            
            return {
                "price": price,
                "change_percent": change_percent,
                "name": name,
                "prev_close": prev_close,
                "volume": float(row.iloc[0]['成交量']),
                "currency": "CNY",
                "source": "akshare"
            }
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching ETF data for {symbol}: {e}")
        return None

def get_cn_stock_realtime_price(symbol: str):
    """
    Get real-time price for CN stock using akshare.
    """
    try:
        # ak.stock_zh_a_spot_em() is heavy. 
        # For single stock, maybe stock_individual_info_em is better?
        # Actually, for reliability and speed, yfinance fast_info is usually better 
        # UNLESS the user specifically wants East Money data sync.
        # User asked for '5' (ETF) specifically. 
        # For '6'/'0'/'3', we can stick to yfinance unless requested otherwise.
        # But let's try to use akshare for consistent CN data if requested.
        pass
    except Exception as e:
        print(e)
    return None

def calculate_atr(symbol: str, period: int = 20):
    """
    Calculate ATR (Average True Range) for a stock/ETF.
    Uses akshare for CN market history, yfinance for others.
    """
    try:
        is_cn = symbol.isdigit() and len(symbol) == 6
        df = None
        
        if is_cn:
            # Try Akshare first
            try:
                # Determine if ETF or Stock based on prefix
                if symbol.startswith('5') or symbol.startswith('15'):
                    # ETF
                    df = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date="20240101", end_date="20500101", adjust="qfq")
                    # Rename columns to standard: Date, Open, High, Low, Close, Volume
                    # Akshare cols: 日期, 开盘, 收盘, 最高, 最低, 成交量, ...
                    df = df.rename(columns={
                        "日期": "Date", "开盘": "Open", "收盘": "Close", 
                        "最高": "High", "最低": "Low", "成交量": "Volume"
                    })
                else:
                    # Stock
                    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20240101", end_date="20500101", adjust="qfq")
                    df = df.rename(columns={
                        "日期": "Date", "开盘": "Open", "收盘": "Close", 
                        "最高": "High", "最低": "Low", "成交量": "Volume"
                    })
            except Exception as e:
                print(f"Akshare history failed for {symbol}: {e}")
                
        # Fallback to yfinance if not CN or Akshare failed
        if df is None:
            yf_symbol = symbol
            if is_cn:
                if symbol.startswith('6') or symbol.startswith('5'): yf_symbol += '.SS'
                else: yf_symbol += '.SZ'
            
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period="3mo") # Get enough data
            df = df.reset_index()
        
        if df is None or df.empty:
            return None

        # Calculate TR
        # TR = Max(H-L, |H-Cp|, |L-Cp|)
        df['High'] = df['High'].astype(float)
        df['Low'] = df['Low'].astype(float)
        df['Close'] = df['Close'].astype(float)
        
        df['PrevClose'] = df['Close'].shift(1)
        df['TR'] = pd.concat([
            df['High'] - df['Low'],
            (df['High'] - df['PrevClose']).abs(),
            (df['Low'] - df['PrevClose']).abs()
        ], axis=1).max(axis=1)
        
        # Calculate ATR
        df['ATR'] = df['TR'].rolling(window=period).mean()
        
        current_atr = df['ATR'].iloc[-1]
        current_price = df['Close'].iloc[-1]
        
        return {
            "atr": float(current_atr),
            "price": float(current_price),
            "suggested_grid_width": float(current_atr), # 1 ATR is a common grid width
            "volatility_ratio": float(current_atr / current_price)
        }
        
    except Exception as e:
        print(f"Error calculating ATR for {symbol}: {e}")
        return None

def fetch_hybrid_data(symbol: str):
    """
    Smart router for data fetching.
    """
    # Fix suffixes for Yfinance
    yf_symbol = symbol
    is_cn_code = symbol.isdigit() and len(symbol) == 6
    
    if is_cn_code:
        # Special handling for ETFs (5xxxxx) -> Akshare
        if symbol.startswith('5'):
            etf_data = get_etf_realtime_price(symbol)
            if etf_data:
                return etf_data
        
        # Suffix logic for yfinance fallback
        if symbol.startswith('5') or symbol.startswith('6'):
            yf_symbol = f"{symbol}.SS"
        elif symbol.startswith('0') or symbol.startswith('3'):
            yf_symbol = f"{symbol}.SZ"
            
    # Fetch from Yfinance
    try:
        ticker = yf.Ticker(yf_symbol)
        # Use fast_info for speed
        info = ticker.fast_info
        try:
            price = info.last_price
            prev_close = info.previous_close
            if price is None: raise ValueError("No price")
            
            return {
                "price": price,
                "change_percent": ((price - prev_close) / prev_close) * 100,
                "name": yf_symbol, # Name might need separate fetch
                "prev_close": prev_close,
                "volume": info.last_volume,
                "currency": info.currency,
                "source": "yfinance"
            }
        except:
            # Fallback to history
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                prev_close = ticker.info.get('previousClose', price)
                return {
                    "price": price,
                    "change_percent": ((price - prev_close) / prev_close) * 100,
                    "name": yf_symbol,
                    "prev_close": prev_close,
                    "volume": hist['Volume'].iloc[-1],
                    "currency": ticker.info.get('currency', 'USD'),
                    "source": "yfinance_hist"
                }
    except Exception as e:
        print(f"Yfinance failed for {yf_symbol}: {e}")
        return None
