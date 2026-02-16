
import akshare as ak
import pandas as pd
import numpy as np
import re

def get_market_data(symbol, start_date, end_date):
    """
    Fetches historical market data for a given stock symbol.
    """
    try:
        # Akshare symbol format needs to be adjusted (e.g., 000300.SH -> sh000300)
        # However, for fund_open_fund_info_em, it seems to work with .SH/.SZ
        # Let's try to fetch stock data first
        is_index = symbol.endswith('.SH') or symbol.endswith('.SZ')
        
        if is_index:
            code = symbol.split('.')[0]
            prefix = 'sh' if symbol.endswith('.SH') else 'sz'
            ak_symbol = f"{prefix}{code}"
            df = ak.stock_zh_a_hist(symbol=ak_symbol, period="daily", start_date=start_date.replace('-', ''), end_date=end_date.replace('-', ''), adjust="qfq")
            df.rename(columns={'日期': 'date', '收盘': 'close'}, inplace=True)
        else: # Assuming it's a fund
            df = ak.fund_open_fund_info_em(fund=symbol, indicator="单位净值走势")
            df.rename(columns={'净值日期': 'date', '单位净值': 'close'}, inplace=True)

        df['date'] = pd.to_datetime(df['date'])
        df = df[['date', 'close']].sort_values('date').set_index('date')
        df['close'] = pd.to_numeric(df['close'])
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def parse_strategy(strategy_text):
    """
    Parses a simple natural language strategy text.
    For now, it only supports monthly investments.
    """
    match = re.search(r'每月.*定投(\d+)元', strategy_text)
    if match:
        return {'type': 'monthly_investment', 'amount': float(match.group(1))}
    return None

def run_backtest(symbol, start_date, end_date, initial_capital, strategy_text, benchmark_symbol='000300.SH'):
    """
    Runs a backtest of a given strategy.
    """
    strategy = parse_strategy(strategy_text)
    if not strategy:
        raise ValueError("Unsupported strategy text")

    # 1. Fetch Data
    strategy_data = get_market_data(symbol, start_date, end_date)
    benchmark_data = get_market_data(benchmark_symbol, start_date, end_date)

    if strategy_data is None or benchmark_data is None:
        raise ValueError("Could not fetch market data")

    # 2. Core Backtesting Logic
    capital = initial_capital
    positions = 0
    net_values = []
    dates = []

    # Commission and Slippage
    commission_rate = 0.0005 # 0.05%
    min_commission = 5
    slippage_rate = 0.001 # 0.1%

    last_month = -1
    for date, row in strategy_data.iterrows():
        current_price = row['close']
        
        # Execute strategy
        if strategy['type'] == 'monthly_investment':
            if date.month != last_month:
                amount = strategy['amount']
                buy_price = current_price * (1 + slippage_rate)
                cost = amount
                commission = cost * commission_rate
                if commission < min_commission: commission = min_commission
                
                shares_to_buy = (cost - commission) / buy_price
                if capital >= cost:
                    capital -= cost
                    positions += shares_to_buy
                last_month = date.month

        # Calculate net value for the day
        current_net_value = capital + positions * current_price
        net_values.append(current_net_value)
        dates.append(date)

    net_value_df = pd.DataFrame({'strategy': net_values}, index=dates)
    net_value_df['strategy'] = net_value_df['strategy'] / initial_capital # Normalize to 1

    # Benchmark
    benchmark_data = benchmark_data.reindex(net_value_df.index).fillna(method='ffill')
    net_value_df['benchmark'] = benchmark_data['close'] / benchmark_data['close'].iloc[0]

    # 3. Calculate Metrics
    total_return = net_value_df['strategy'].iloc[-1] - 1
    holding_period_years = (net_value_df.index[-1] - net_value_df.index[0]).days / 365.25
    annualized_return = (1 + total_return) ** (1 / holding_period_years) - 1 if holding_period_years > 0 else 0

    cumulative_max = net_value_df['strategy'].cummax()
    drawdown = (net_value_df['strategy'] - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min()

    daily_returns = net_value_df['strategy'].pct_change().dropna()
    sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0

    # Win rate (days the strategy went up)
    win_rate = (daily_returns > 0).sum() / len(daily_returns) if len(daily_returns) > 0 else 0

    metrics = {
        'annualized_return': annualized_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'win_rate': win_rate,
    }

    return {
        'metrics': metrics,
        'net_value_data': net_value_df.reset_index().rename(columns={'index': 'date'}).to_dict('records')
    }
