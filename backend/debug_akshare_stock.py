import akshare as ak
import pandas as pd

try:
    print("Fetching ak.stock_zh_a_spot_em()...")
    df = ak.stock_zh_a_spot_em()
    print("Columns:", df.columns.tolist())
    # Check a sample row
    print("Sample row:", df.head(1).to_dict('records')[0])
except Exception as e:
    print("Error:", e)
