
import requests
import json
import logging
import akshare as ak
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NOTE: Since the user provided a Table Link and not a Webhook URL, 
# we need a placeholder. A Bitable write usually requires an Open API call
# or a specific Automation Webhook.
# We will assume the user has set up an Automation Webhook that accepts JSON.
FEISHU_WEBHOOK_URL = "YOUR_FEISHU_WEBHOOK_URL_HERE" 

def fetch_etf_data(symbol: str = "512100"):
    """
    Fetch close price and change pct for a given ETF symbol.
    Uses Akshare for real-time data.
    """
    try:
        # 512100 is typically an ETF (e.g., China Securities 500 ETF or similar)
        # We need to determine if it's .SS or .SZ for Yahoo, but for Akshare we use raw code.
        # Akshare's fund_etf_spot_em returns all ETFs. We filter.
        
        # This is heavy, maybe we can use a lighter endpoint if available.
        # But for daily scheduled task, it's fine.
        df = ak.fund_etf_spot_em()
        
        # Filter by code
        row = df[df['代码'] == symbol]
        
        if row.empty:
            logger.error(f"Symbol {symbol} not found in Akshare ETF data.")
            return None
            
        # Extract data
        # Columns usually: 序号, 代码, 名称, 最新价, 涨跌额, 涨跌幅, ...
        latest_price = float(row.iloc[0]['最新价'])
        change_pct = float(row.iloc[0]['涨跌幅'])
        name = row.iloc[0]['名称']
        
        return {
            "symbol": symbol,
            "name": name,
            "close": latest_price,
            "change_pct": change_pct,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
    except Exception as e:
        logger.error(f"Error fetching ETF data: {e}")
        return None

def push_to_feishu_bitable(webhook_url: str = FEISHU_WEBHOOK_URL):
    """
    Fetches data for 512100 and pushes to Feishu via Webhook.
    """
    if webhook_url == "YOUR_FEISHU_WEBHOOK_URL_HERE":
        logger.warning("Feishu Webhook URL is not set. Skipping push.")
        return {"status": "skipped", "reason": "Webhook URL missing"}

    data = fetch_etf_data("512100")
    if not data:
        return {"status": "failed", "reason": "Data fetch failed"}

    # Prepare payload
    # The structure depends on how the Feishu Automation is set up.
    # We will send a generic JSON object.
    payload = {
        "fields": {
            "日期": data["date"],
            "代码": data["symbol"],
            "名称": data["name"],
            "收盘价": data["close"],
            "涨跌幅": data["change_pct"]
            # Add grid stats if available (Mocking for now as we don't have active grid stats here)
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        logger.info(f"Successfully pushed to Feishu: {response.text}")
        return {"status": "success", "response": response.json()}
    except Exception as e:
        logger.error(f"Failed to push to Feishu: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    # Test run
    print(fetch_etf_data())
