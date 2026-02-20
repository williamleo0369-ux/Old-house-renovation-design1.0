import requests
import os
import logging
import time
import json

logger = logging.getLogger(__name__)

# Default Configuration from User
DEFAULT_APP_TOKEN = "IsL0w4WpDiYGhekvnKAcLEHJn9c"
DEFAULT_TABLE_ID = "tblCmtkrbs2KxbqP"
DEFAULT_PORTFOLIO_APP_TOKEN = "PYTbbiGEgaVqvNsNXmmcDhkPnhg"
DEFAULT_PORTFOLIO_TABLE_ID = "tblAyqYazaUimRnc" # New table for positions
DEFAULT_APP_ID = "cli_a9045d9277f8dcc1"
DEFAULT_APP_SECRET = "KHpqxcUp7iyiugqxPHS0Tc0xC7ioXgsw"

class FeishuIntegrator:
    def __init__(self):
        self.app_id = os.environ.get("FEISHU_APP_ID", DEFAULT_APP_ID)
        self.app_secret = os.environ.get("FEISHU_APP_SECRET", DEFAULT_APP_SECRET)
        self.app_token = os.environ.get("FEISHU_APP_TOKEN", DEFAULT_APP_TOKEN)
        self.table_id = os.environ.get("FEISHU_TABLE_ID", DEFAULT_TABLE_ID)
        self.portfolio_app_token = os.environ.get("FEISHU_PORTFOLIO_APP_TOKEN", DEFAULT_PORTFOLIO_APP_TOKEN)
        self.portfolio_table_id = os.environ.get("FEISHU_PORTFOLIO_TABLE_ID", DEFAULT_PORTFOLIO_TABLE_ID)
        
        self._tenant_access_token = None
        self._token_expire_time = 0
        self._record_id_map = {} # Cache for symbol -> record_id
        self._field_id_map = None # Cache for field name -> field_id

    def _get_field_id_map(self):
        """
        Get and cache the mapping of field names to field IDs for the table.
        """
        if self._field_id_map is not None:
            return self._field_id_map

        token = self._get_tenant_access_token()
        if not token:
            return {}

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            if data.get("code") == 0:
                field_map = {}
                items = data.get("data", {}).get("items", [])
                if not items:
                    logger.warning(f"Feishu API returned no fields (items). Full response: {data}")
                
                for field in items:
                    field_map[field.get("field_name")] = field.get("field_id")
                self._field_id_map = field_map
                logger.info(f"Successfully fetched and cached field ID map: {self._field_id_map}")
                return self._field_id_map
            else:
                logger.error(f"Failed to get Feishu table meta: {data}")
                return {}
        except Exception as e:
            logger.error(f"Error fetching Feishu table meta: {e}")
            return {}

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
                    record_id = item.get("record_id")
                    fields = item.get("fields", {})
                    logger.info(f"DEBUG: Raw field value for '股票代码和名称': {fields.get('股票代码和名称')} (Type: {type(fields.get('股票代码和名称'))})")
                    # Parse symbol from "股票代码和名称"
                    # Example: "黄金ETF 518880"
                    # Or simply try to get "股票代码" if exists
                    symbol = fields.get("股票代码")
                    
                    if not symbol:
                        # Try parsing from "股票代码和名称"
                        combined = fields.get("股票代码和名称") # Get raw value
                        if not combined:
                            logger.warning(f"Skipping record {item.get('record_id')} because key symbol fields are empty.")
                            continue

                        if combined:
                            import re
                            # Look for 6 digit code
                            match = re.search(r'\d{6}', str(combined))
                            if match:
                                symbol = match.group(0)
                    
                    if not symbol:
                        # Fallback legacy
                        symbol = fields.get("代码") or fields.get("Symbol") or fields.get("code")

                    if symbol and record_id:
                        # Clean symbol (e.g., ensure string)
                        clean_symbol = str(symbol).strip()
                        symbols.append(clean_symbol)
                        self._record_id_map[clean_symbol] = record_id
                
                if not data.get("data", {}).get("has_more"):
                    break
                
                page_token = data.get("data", {}).get("page_token")
                
            logger.info(f"Loaded {len(symbols)} symbols from Feishu.")
            return symbols
            
        except Exception as e:
            logger.error(f"Exception loading from Feishu: {e}")
            return []

    def push_record(self, fields):
        """
        Push a single record to Bitable using field IDs.
        """
        token = self._get_tenant_access_token()
        if not token:
            return

        # Let's try sending the raw field names directly, as some Feishu APIs support this.
        # This bypasses any potential issues with field ID mapping or type mismatches.
        payload_fields = fields

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "fields": payload_fields
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()
            if data.get("code") == 0:
                logger.info(f"Successfully pushed record to Feishu.")
                print(f"[Feishu] Successfully saved backtest results for {fields.get('股票代码')} to Feishu.")
            else:
                logger.error(f"Failed to push to Feishu: {data}")
        except Exception as e:
            logger.error(f"Error pushing to Feishu: {e}")

    def update_record(self, record_id, fields):
        """
        Update a single record in Bitable using field IDs.
        """
        token = self._get_tenant_access_token()
        if not token:
            return

        field_id_map = self._get_field_id_map()
        if not field_id_map:
            logger.error("Could not get field ID map. Aborting update.")
            return

        # Translate field names to field IDs
        payload_fields = {}
        for name, value in fields.items():
            field_id = field_id_map.get(name)
            if field_id:
                payload_fields[field_id] = value
            else:
                logger.warning(f"Field name '{name}' not found in table meta for update. Skipping this field.")

        if not payload_fields:
            logger.error("No valid fields to update after name->ID translation. Aborting.")
            return

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "fields": payload_fields
        }
        
        try:
            response = requests.put(url, headers=headers, json=payload)
            data = response.json()
            if data.get("code") == 0:
                logger.info(f"Successfully updated record {record_id} in Feishu.")
            else:
                logger.error(f"Failed to update record {record_id} in Feishu: {data}")
        except Exception as e:
            logger.error(f"Error updating record {record_id} in Feishu: {e}")

    def get_positions(self):
        """
        Read all records from the portfolio table.
        """
        token = self._get_tenant_access_token()
        if not token:
            return []

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.portfolio_app_token}/tables/{self.portfolio_table_id}/records"
        headers = {"Authorization": f"Bearer {token}"}
        
        positions = []
        page_token = None
        try:
            while True:
                params = {"page_size": 100}
                if page_token:
                    params["page_token"] = page_token

                response = requests.get(url, headers=headers, params=params)
                data = response.json()
                
                if data.get("code") != 0:
                    logger.error(f"Error reading Feishu portfolio table: {data}")
                    break
                
                items = data.get("data", {}).get("items", [])
                for item in items:
                    # Add record_id to the fields for future reference (e.g., deletion)
                    positions.append(item)
                
                if not data.get("data", {}).get("has_more"):
                    break
                page_token = data.get("data", {}).get("page_token")
                
            logger.info(f"Loaded {len(positions)} positions from Feishu portfolio.")
            return positions
        except Exception as e:
            logger.error(f"Exception loading portfolio from Feishu: {e}", exc_info=True)
            return []

    def add_position(self, record_data):
        """
        Add a single position record to the portfolio table.
        record_data should be a dict like:
        {"股票代码": "000001", "持仓数量": 100, "成本单价": 10.5}
        """
        token = self._get_tenant_access_token()
        if not token:
            return None

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.portfolio_app_token}/tables/{self.portfolio_table_id}/records"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"fields": record_data}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()
            if data.get("code") == 0:
                logger.info(f"Successfully added position: {record_data.get('股票代码')}")
                new_record = data.get("data", {}).get("record")
                if new_record:
                    # The returned record from Feishu contains the fields we just added
                    logger.info(f"Successfully added position: {new_record.get('fields', {}).get('股票代码')}")
                    return new_record
                return None
            else:
                logger.error(f"Failed to add position to Feishu: {data}")
                return None
        except Exception as e:
            logger.error(f"Error adding position to Feishu: {e}", exc_info=True)
            return None

    def delete_position(self, record_id):
        """
        Delete a single record from the portfolio table.
        """
        token = self._get_tenant_access_token()
        if not token:
            return False

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.portfolio_app_token}/tables/{self.portfolio_table_id}/records/{record_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.delete(url, headers=headers)
            data = response.json()
            if data.get("code") == 0:
                logger.info(f"Successfully deleted position record {record_id}.")
                return True
            else:
                logger.error(f"Failed to delete position {record_id} from Feishu: {data}")
                return False
        except Exception as e:
            logger.error(f"Error deleting position {record_id} from Feishu: {e}", exc_info=True)
            return False

# Global Instance
feishu_integrator = FeishuIntegrator()

def push_to_feishu_bitable(symbols=None):
    """
    Daily job to push market data to Feishu.
    Args:
        symbols: Optional list of symbols to sync. If None, fetches from Feishu.
    """
    from market_data import fetch_hybrid_data
    import datetime
    # Import inside function to avoid circular dependency
    from scheduler import get_all_strategies_status
    
    logger.info("Daily Feishu Report Job Triggered")
    
    # 1. Determine symbols to process
    if not symbols:
        # Fallback: Read from Feishu if not provided (e.g. scheduled job)
        symbols = feishu_integrator.load_favorites_from_feishu()
    
    if not symbols:
        logger.warning("No symbols found to update.")
        return

    # 2. Get Strategy Status for detailed metrics
    strategies = get_all_strategies_status()
    # Create a lookup dict: symbol -> strategy_data
    strat_map = {s['symbol']: s for s in strategies}

    # 3. Fetch data and push
    # Feishu Bitable "Date" field often requires specific format or timestamp in ms
    # But user schema says "Text" for everything?
    # Schema check: All fields are Text.
    
    for sym in symbols:
        try:
            data = fetch_hybrid_data(sym)
            if data:
                # Get strategy data if available
                strat = strat_map.get(sym, {})
                
                # Format Name + Code
                name = data.get("name", "")
                combined_name = f"{name} {sym}"
                
                # Format Numeric Values
                price = data.get("price", 0)
                change = data.get("change_percent", 0)
                trade_count = strat.get("trade_count", 0)
                total_profit = strat.get("total_profit", 0.0)
                
                # Convert to formatted strings
                fields = {
                    "股票代码和名称": combined_name,
                    "收盘价": f"{price:.3f}",
                    "涨跌幅": f"{change:.2f}%",
                    "网格成交单数": str(trade_count),
                    "总利润": f"{total_profit:.3f}",
                    "总结": "" # Optional
                }
                
                feishu_integrator.push_record(fields)
                time.sleep(0.3) # Avoid rate limit
        except Exception as e:
            logger.error(f"Error processing {sym} for Feishu: {e}")

