
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
    Get real-time price for ETF using akshare (Sina source).
    Symbol should be 6 digits (e.g., '510300').
    """
    global ETF_LIST_CACHE
    
    try:
        # Check cache first (1 min cache)
        if ETF_LIST_CACHE["data"] is not None and time.time() - ETF_LIST_CACHE["timestamp"] < 60:
            df = ETF_LIST_CACHE["data"]
        else:
            # Fetch all ETF spot data from Sina (Better reliability than EastMoney in some envs)
            df = ak.fund_etf_category_sina(symbol="ETF基金")
            ETF_LIST_CACHE["data"] = df
            ETF_LIST_CACHE["timestamp"] = time.time()
        
        # Filter for the symbol
        # Sina returns codes like 'sh518880', 'sz159998'. 
        # We need to match '518880' inside 'sh518880'
        
        # Create a clean code column if not exists
        if 'clean_code' not in df.columns:
            df['clean_code'] = df['代码'].apply(lambda x: x.replace('sh', '').replace('sz', ''))
            
        row = df[df['clean_code'] == symbol]
        
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
                "source": "akshare_sina"
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

NAME_CACHE = {}
ETF_CACHE_POPULATED = False

def get_cn_name(symbol):
    """
    Get Chinese name for a stock symbol using Akshare (Cached).
    """
    if symbol in NAME_CACHE:
        return NAME_CACHE[symbol]
    
    try:
        # ETF Handling (5xxxxx or 15xxxx)
        if symbol.startswith("5") or symbol.startswith("15"):
             global ETF_CACHE_POPULATED
             if not ETF_CACHE_POPULATED:
                 try:
                     # Fetch all ETFs from Sina (Fast & Reliable)
                     df = ak.fund_etf_category_sina(symbol="ETF基金")
                     # df['代码'] is like 'sh518880', 'sz159998'
                     for _, row in df.iterrows():
                         raw_code = str(row['代码'])
                         name = str(row['名称'])
                         # Strip sh/sz prefix
                         clean_code = raw_code.replace("sh", "").replace("sz", "")
                         NAME_CACHE[clean_code] = name
                     
                     ETF_CACHE_POPULATED = True
                     
                     # Check again
                     if symbol in NAME_CACHE:
                         return NAME_CACHE[symbol]
                 except Exception as e:
                     print(f"ETF Name Fetch Error: {e}")
                     # Fallback for common ones
                     fallback_map = {
                         "518880": "黄金ETF",
                         "512100": "中证1000ETF", 
                         "588000": "科创50ETF",
                         "513100": "纳指ETF",
                         "513050": "中概互联ETF"
                     }
                     if symbol in fallback_map:
                         NAME_CACHE[symbol] = fallback_map[symbol]
                         return fallback_map[symbol]
        
        # Stock Handling
        else:
            df = ak.stock_individual_info_em(symbol=symbol)
            name_row = df[df['item'] == "股票简称"]
            if not name_row.empty:
                name = name_row.iloc[0]['value']
                NAME_CACHE[symbol] = name
                return name
                
    except Exception as e:
        # print(f"Name fetch error for {symbol}: {e}")
        pass
    
    return None

def fetch_hybrid_data(symbol: str):
    """
    Smart router for data fetching.
    """
    # Fix suffixes for Yfinance
    yf_symbol = symbol
    
    # Check if it is a CN code (either pure 6 digits or with .SS/.SZ suffix)
    clean_symbol = symbol.split('.')[0]
    is_cn_code = False
    
    if clean_symbol.isdigit() and len(clean_symbol) == 6:
        is_cn_code = True
        # If input was pure digits, we might need to add suffix for yfinance
        if symbol.isdigit():
             if clean_symbol.startswith('5') or clean_symbol.startswith('6'):
                yf_symbol = f"{clean_symbol}.SS"
             elif clean_symbol.startswith('0') or clean_symbol.startswith('3'):
                yf_symbol = f"{clean_symbol}.SZ"
    
    if is_cn_code:
        # Special handling for ETFs (5xxxxx) -> Akshare
        if clean_symbol.startswith('5'):
            etf_data = get_etf_realtime_price(clean_symbol)
            if etf_data:
                # Try to attach name if available
                cn_name = get_cn_name(clean_symbol)
                if cn_name: etf_data['name'] = cn_name
                return etf_data
            
    # Fetch from Yfinance
    try:
        ticker = yf.Ticker(yf_symbol)
        # Use fast_info for speed
        info = ticker.fast_info
        try:
            price = info.last_price
            prev_close = info.previous_close
            if price is None: raise ValueError("No price")
            
            # Try to get a good name
            name = yf_symbol
            if is_cn_code:
                # Try Akshare cache or fetch using the clean 6-digit code
                cn_name = get_cn_name(clean_symbol)
                if cn_name:
                    name = cn_name
                else:
                    # Fallback to yfinance info (might be slow/english)
                    # We skip ticker.info call to keep it fast unless necessary
                    pass
            
            return {
                "price": price,
                "change_percent": ((price - prev_close) / prev_close) * 100,
                "name": name, 
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
                
                # Try name again
                name = yf_symbol
                if is_cn_code:
                     cn_name = get_cn_name(clean_symbol)
                     if cn_name: name = cn_name
                
                return {
                    "price": price,
                    "change_percent": ((price - prev_close) / prev_close) * 100,
                    "name": name,
                    "prev_close": prev_close,
                    "volume": hist['Volume'].iloc[-1],
                    "currency": ticker.info.get('currency', 'USD'),
                    "source": "yfinance_hist"
                }
    except Exception as e:
        print(f"Yfinance failed for {yf_symbol}: {e}")
        return None
