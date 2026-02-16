import akshare as ak
import pandas as pd

try:
    print("Fetching ak.stock_info_global_cls()...")
    df = ak.stock_info_global_cls(symbol="全部")
    print("Columns:", df.columns.tolist())
    print("First row:", df.iloc[0].to_dict())
except Exception as e:
    print("Error:", e)
