# backend/backtester.py

import logging
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from feishu_integration import feishu_integrator

logger = logging.getLogger(__name__)

def calculate_dca_backtest(symbol: str, amount: float, frequency: str, start_date: str, smart_dca: bool = False):
    """
    Performs a Dollar-Cost Averaging (DCA) backtest for a given stock symbol.

    Args:
        symbol (str): The stock symbol (e.g., '512100').
        amount (float): The amount to invest at each interval.
        frequency (str): The investment frequency ('weekly' or 'monthly').
        start_date (str): The start date for the backtest (YYYY-MM-DD).
        smart_dca (bool): If True, increases investment when price is below 20-day MA.

    Returns:
        dict: A dictionary containing the backtest results.
    """
    # Akshare expects symbols like 'sh512100' or 'sz159915'
    # We need to determine the market prefix
    market_prefix = "sh" if symbol.startswith(('5', '6')) else "sz"
    ak_symbol = f"{market_prefix}{symbol}"
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date_formatted = start_date.replace('-', '')

    logger.info(f"Running DCA backtest for {ak_symbol} from {start_date} with amount {amount} and frequency {frequency}")

    try:
        # Fetch historical data
        hist_df = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start_date_formatted, end_date=end_date, adjust="qfq")
        if hist_df.empty:
            logger.error(f"Could not fetch historical data for {ak_symbol}. It might be an invalid symbol or date range.")
            return {"error": f"无法获取 {ak_symbol} 的历史数据。"}
        
        # Data preparation
        hist_df['日期'] = pd.to_datetime(hist_df['日期'])
        hist_df.set_index('日期', inplace=True)
        hist_df['收盘'] = pd.to_numeric(hist_df['收盘'])
        
        # Calculate 20-day Moving Average for Smart DCA
        if smart_dca:
            hist_df['MA20'] = hist_df['收盘'].rolling(window=20).mean()

        # Simulate investment
        investments = []
        last_investment_date = None

        # Determine investment days
        if frequency == 'weekly':
            investment_dates = pd.date_range(start=start_date, end=datetime.now(), freq='W-MON') # Invest every Monday
        elif frequency == 'monthly':
            investment_dates = pd.date_range(start=start_date, end=datetime.now(), freq='MS') # Invest on the 1st of every month
        else:
            return {"error": "无效的定投频率。请选择 'weekly' 或 'monthly'。"}

        total_cost = 0
        total_shares = 0

        for investment_date in investment_dates:
            # Find the actual trading day closest to the planned investment date
            trading_day = hist_df.index[hist_df.index.searchsorted(investment_date)]
            
            if trading_day and (last_investment_date is None or trading_day > last_investment_date):
                price = hist_df.loc[trading_day, '收盘']
                investment_amount = amount

                # Smart DCA logic
                if smart_dca and 'MA20' in hist_df.columns and not pd.isna(hist_df.loc[trading_day, 'MA20']):
                    if price < hist_df.loc[trading_day, 'MA20']:
                        investment_amount *= 1.2 # Increase investment by 20%
                
                shares_bought = investment_amount / price
                total_cost += investment_amount
                total_shares += shares_bought
                last_investment_date = trading_day

                investments.append({
                    "date": trading_day.strftime('%Y-%m-%d'),
                    "cost": investment_amount,
                    "price": price,
                    "shares": shares_bought
                })

        if total_shares == 0:
            return {"error": "在指定时间范围内没有发生任何投资。"}

        # Calculate final results
        current_price = hist_df.iloc[-1]['收盘']
        market_value = total_shares * current_price
        total_profit = market_value - total_cost
        profit_margin = (total_profit / total_cost) * 100 if total_cost > 0 else 0
        avg_cost_price = total_cost / total_shares

        # --- Sync to Feishu ---
        try:
            # We need the record_id for the symbol. The integrator should have it cached.
            if not feishu_integrator._record_id_map:
                # If cache is empty, load it. This is a fallback.
                logger.info("Feishu record ID map is empty, loading it now.")
                feishu_integrator.load_favorites_from_feishu()
            
            record_id = feishu_integrator._record_id_map.get(symbol)
            
            if record_id:
                # The user wants to store "持仓成本线" and "最佳定投频率"
                # We have the cost line (avg_cost_price). 
                # "Best frequency" isn't calculated here, so we'll just pass the one used.
                fields_to_update = {
                    "持仓成本线": f"{avg_cost_price:.3f}",
                    "最佳定投频率": frequency # Storing the frequency used for this backtest
                }
                feishu_integrator.update_record(record_id, fields_to_update)
                logger.info(f"Successfully triggered Feishu update for {symbol} with cost line {avg_cost_price:.3f}")
            else:
                logger.warning(f"Could not find record_id for symbol {symbol} to update Feishu.")

        except Exception as e:
            logger.error(f"Failed to sync backtest results to Feishu for symbol {symbol}: {e}")
        # --- End of Sync ---

        return {
            "total_cost": round(total_cost, 2),
            "total_shares": round(total_shares, 4),
            "market_value": round(market_value, 2),
            "total_profit": round(total_profit, 2),
            "profit_margin": round(profit_margin, 2),
            "average_cost_price": round(avg_cost_price, 3),
            "current_price": round(current_price, 3),
            "investment_log": investments
        }

    except Exception as e:
        logger.error(f"An error occurred during backtest for {ak_symbol}: {e}")
        return {"error": f"回测期间发生错误: {e}"}

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Example usage:
    backtest_results = calculate_dca_backtest(
        symbol='512100',
        amount=1000,
        frequency='weekly',
        start_date='2023-01-01',
        smart_dca=True
    )
    import json
    print("--- DCA Backtest Results ---")
    print(json.dumps(backtest_results, indent=2, ensure_ascii=False))
    print("---------------------------")
