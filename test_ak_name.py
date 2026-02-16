import akshare as ak
try:
    df = ak.stock_individual_info_em(symbol="600519")
    print(df)
except Exception as e:
    print(e)
