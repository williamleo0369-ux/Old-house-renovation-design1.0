# backend/stock_screener.py

import pandas as pd
import akshare as ak
import time

import talib
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Constants ---
CACHE_TTL = 3600  # 1 hour
KLINE_CACHE_TTL = 86400 # 24 hours for historical data


# --- Cache ---
_stock_list_cache = {"timestamp": 0, "data": None}
_stock_data_cache = {}

class StockScreener:
    def __init__(self):
        pass

    def get_all_stocks(self):
        """
        Get a list of all A-share stocks.
        Uses a cache to avoid frequent API calls.
        """
        now = time.time()
        if now - _stock_list_cache["timestamp"] < CACHE_TTL and _stock_list_cache["data"] is not None:
            return _stock_list_cache["data"]

        try:
            # Fetch real-time stock list
            stock_df = ak.stock_zh_a_spot_em()
            # We only need symbol and name for the list
            stock_df = stock_df[['代码', '名称']]
            _stock_list_cache["data"] = stock_df
            _stock_list_cache["timestamp"] = now
            print(f"Successfully fetched and cached {len(stock_df)} stocks.")
            return stock_df
        except Exception as e:
            print(f"Error fetching stock list: {e}")
            return pd.DataFrame()

    def get_fundamental_data(self, stocks_df):
        """
        Get fundamental data for all stocks and merge it.
        """
        now = time.time()
        # Use a simple cache check based on the number of stocks
        cache_key = f"fundamental_{len(stocks_df)}"
        if cache_key in _stock_data_cache and now - _stock_data_cache[cache_key]["timestamp"] < CACHE_TTL:
            return _stock_data_cache[cache_key]["data"]

        try:
            # Fetch fundamental data
            fund_df = ak.stock_zh_a_spot_em()
            # Select relevant columns
            fund_df = fund_df[['代码', '市盈率-动态', '市净率', '总市值']]
            fund_df.rename(columns={
                '市盈率-动态': 'pe_ratio',
                '市净率': 'pb_ratio',
                '总市值': 'market_cap'
            }, inplace=True)

            # --- Fetch ROE data ---
            # This is a separate, more detailed interface
            roe_df = ak.stock_financial_analysis_indicator(symbol="所有", indicator="年度")
            roe_df = roe_df[['股票代码', '净资产收益率(%)']]
            roe_df.rename(columns={
                '股票代码': '代码',
                '净资产收益率(%)': 'roe'
            }, inplace=True)
            # The ROE data might have duplicates if multiple years are returned, get the latest one
            roe_df = roe_df.drop_duplicates(subset=['代码'], keep='first')

            # --- Merge all data ---
            merged_df = pd.merge(stocks_df, fund_df, on='代码')
            merged_df = pd.merge(merged_df, roe_df, on='代码', how='left') # Left join to not lose stocks if ROE is missing


            # Cache the result
            _stock_data_cache[cache_key] = {"timestamp": now, "data": merged_df}
            print(f"Successfully fetched and cached fundamental data for {len(merged_df)} stocks.")
            return merged_df
        except Exception as e:
            print(f"Error fetching fundamental data: {e}")
            return stocks_df # Return original df as fallback

    def _get_stock_kline(self, symbol):
        """Helper to fetch and cache k-line data for a single stock."""
        now = time.time()
        cache_key = f"kline_{symbol}"
        if cache_key in _stock_data_cache and now - _stock_data_cache[cache_key]["timestamp"] < KLINE_CACHE_TTL:
            return _stock_data_cache[cache_key]["data"]
        
        try:
            # akshare uses 'sh' or 'sz' prefix for Shanghai/Shenzhen, but our list doesn't have it.
            # We need to add it based on the stock code.
            # 6 for Shanghai, 0/3 for Shenzhen
            prefix_symbol = f"sh{symbol}" if symbol.startswith('6') else f"sz{symbol}"
            
            # Fetch daily k-line data for the last year
            kline_df = ak.stock_zh_a_hist(symbol=prefix_symbol, period="daily", adjust="qfq")
            if kline_df.empty:
                return None

            _stock_data_cache[cache_key] = {"timestamp": now, "data": kline_df}
            return kline_df
        except Exception as e:
            # print(f"Error fetching k-line for {symbol}: {e}") # This can be very noisy
            return None

    def _calculate_single_stock_indicators(self, stock_row):
        """Helper to calculate indicators for a single stock row."""
        symbol = stock_row['代码']
        kline_df = self._get_stock_kline(symbol)

        if kline_df is None or kline_df.empty or len(kline_df) < 60:
            return symbol, None, None, 'neutral'

        close_prices = kline_df['收盘']
        ma20 = talib.SMA(close_prices, timeperiod=20).iloc[-1]
        ma60 = talib.SMA(close_prices, timeperiod=60).iloc[-1]

        # MACD Calculation
        macd, macdsignal, _ = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
        
        macd_signal_status = 'neutral'
        if not pd.isna(macd.iloc[-1]) and not pd.isna(macdsignal.iloc[-1]) and not pd.isna(macd.iloc[-2]) and not pd.isna(macdsignal.iloc[-2]):
            # Golden Cross: MACD crosses above signal line
            if macd.iloc[-2] < macdsignal.iloc[-2] and macd.iloc[-1] > macdsignal.iloc[-1]:
                macd_signal_status = 'golden_cross'
            # Death Cross: MACD crosses below signal line
            elif macd.iloc[-2] > macdsignal.iloc[-2] and macd.iloc[-1] < macdsignal.iloc[-1]:
                macd_signal_status = 'death_cross'

        return symbol, ma20, ma60, macd_signal_status

    def calculate_technical_indicators(self, df):
        """
        Calculate technical indicators (MA, MACD) for the given DataFrame of stocks.
        Uses ThreadPoolExecutor for parallel processing.
        """
        results = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Create a future for each stock
            future_to_stock = {executor.submit(self._calculate_single_stock_indicators, row): row for _, row in df.iterrows()}
            
            print(f"Calculating technical indicators for {len(df)} stocks...")
            # Process completed futures
            for future in as_completed(future_to_stock):
                try:
                    symbol, ma20, ma60, macd_signal = future.result()
                    results[symbol] = {'ma20': ma20, 'ma60': ma60, 'macd_signal': macd_signal}
                except Exception as e:
                    stock_code = future_to_stock[future]['代码']
                    print(f"Error processing stock {stock_code}: {e}")

        # Create new columns and map the results
        df_tech = df.copy()
        df_tech['ma20'] = df_tech['代码'].map(lambda x: results.get(x, {}).get('ma20'))
        df_tech['ma60'] = df_tech['代码'].map(lambda x: results.get(x, {}).get('ma60'))
        df_tech['macd_signal'] = df_tech['代码'].map(lambda x: results.get(x, {}).get('macd_signal', 'neutral'))

        print("Finished calculating technical indicators.")
        return df_tech




# --- Singleton Instance ---
screener = StockScreener()

if __name__ == '__main__':
    # --- Test --- 
    all_stocks = screener.get_all_stocks()
    print("All A-share stocks:")
    print(all_stocks.head())
