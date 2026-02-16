
import logging
from feishu_integration import FeishuIntegrator
from datetime import datetime

# Configure logging to show info level messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def restore():
    """
    Restores a predefined list of ETFs to the Feishu Bitable watchlist.
    It first loads the existing symbols to avoid creating duplicates.
    """
    integrator = FeishuIntegrator()
    
    # The list of ETFs that the user wants in their watchlist
    watchlist_to_restore = {
        "512100": "中证1000",
        "518880": "黄金ETF",
        "513180": "纳指ETF",
        "588000": "科创50",
    }

    print("Step 1: Loading existing watchlist from Feishu to prevent duplicates...")
    # This also populates the field_id_map inside the integrator
    existing_symbols = integrator.load_favorites_from_feishu()
    print(f"Step 2: Found {len(existing_symbols)} existing symbols: {existing_symbols}")

    symbols_added_count = 0
    for code, name in watchlist_to_restore.items():
        if code in existing_symbols:
            print(f"- Symbol {code} ({name}) already exists in the watchlist. Skipping.")
        else:
            print(f"+ Adding symbol {code} ({name}) to the watchlist...")
            # Based on user feedback, the table requires a date. We will also add today's date.
            fields = {
                "DATA日期": int(datetime.now().timestamp() * 1000), # Feishu expects timestamp in milliseconds
                "股票代码": code
            }
            integrator.push_record(fields)
            symbols_added_count += 1
    
    print(f"Step 3: Watchlist restoration process completed. Added {symbols_added_count} new symbol(s).")

if __name__ == "__main__":
    restore()
