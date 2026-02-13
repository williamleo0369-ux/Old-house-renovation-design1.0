import requests
import os
import logging
import time
import json

logger = logging.getLogger(__name__)

# Default Configuration from User
DEFAULT_APP_TOKEN = "IsL0w4WpDiYGhekvnKAcLEHJn9c"
DEFAULT_TABLE_ID = "tblCmtkrbs2KxbqP"

class FeishuIntegrator:
    def __init__(self):
        self.app_id = os.environ.get("FEISHU_APP_ID")
        self.app_secret = os.environ.get("FEISHU_APP_SECRET")
        self.app_token = os.environ.get("FEISHU_APP_TOKEN", DEFAULT_APP_TOKEN)
        self.table_id = os.environ.get("FEISHU_TABLE_ID", DEFAULT_TABLE_ID)
        self.webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
        
        self._tenant_access_token = None
        self._token_expire_time = 0

    def _get_tenant_access_token(self):
        """
        Get or refresh tenant access token
        """
        if not self.app_id or not self.app_secret:
            logger.warning("Feishu App ID or Secret not configured. Skipping API calls.")
            return None

        if self._tenant_access_token and time.time() < self._token_expire_time:
            return self._tenant_access_token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()
            
            if data.get("code") == 0:
                self._tenant_access_token = data.get("tenant_access_token")
                # Expire a bit earlier than actual to be safe
                self._token_expire_time = time.time() + data.get("expire", 7200) - 60
                return self._tenant_access_token
            else:
                logger.error(f"Failed to get Feishu token: {data}")
                return None
        except Exception as e:
            logger.error(f"Error fetching Feishu token: {e}")
            return None

    def load_favorites_from_feishu(self):
        """
        Read watchlist from Feishu Bitable.
        Returns a list of symbols.
        """
        token = self._get_tenant_access_token()
        if not token:
            return []

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # We need to find the column that contains the symbol.
        # Assuming column name is "Code" or "代码" or "Symbol"
        # We will fetch all fields and look for a likely candidate in the first record or just grab the first text field.
        # For simplicity, let's fetch and try to parse.
        
        symbols = []
        page_token = None
        
        try:
            while True:
                params = {"page_size": 100}
                if page_token:
                    params["page_token"] = page_token

                response = requests.get(url, headers=headers, params=params)
                data = response.json()
                
                if data.get("code") != 0:
                    logger.error(f"Error reading Feishu table: {data}")
                    break
                
                items = data.get("data", {}).get("items", [])
                for item in items:
                    fields = item.get("fields", {})
                    # Try common field names
                    symbol = fields.get("代码") or fields.get("Symbol") or fields.get("股票代码") or fields.get("code")
                    if symbol:
                        # Clean symbol (e.g., ensure string)
                        symbols.append(str(symbol).strip())
                
                if not data.get("data", {}).get("has_more"):
                    break
                
                page_token = data.get("data", {}).get("page_token")
                
            logger.info(f"Loaded {len(symbols)} symbols from Feishu.")
            return symbols
            
        except Exception as e:
            logger.error(f"Exception loading from Feishu: {e}")
            return []

    def sync_to_webhook(self, symbol, name="", action="add"):
        """
        Send data to Feishu Webhook.
        """
        if not self.webhook_url:
            logger.warning("Feishu Webhook URL not configured.")
            return

        payload = {
            "symbol": symbol,
            "name": name,
            "action": action,
            "timestamp": int(time.time())
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 200:
                logger.info(f"Successfully synced {symbol} to Feishu Webhook.")
            else:
                logger.error(f"Failed to sync to Feishu Webhook: {response.text}")
        except Exception as e:
            logger.error(f"Error sending to Feishu Webhook: {e}")

# Global Instance
feishu_integrator = FeishuIntegrator()
