import requests
import logging
import os

logger = logging.getLogger(__name__)

class WeChatNotifier:
    def __init__(self, uid=None):
        self.uid = uid
        self.api_url = "https://wxpusher.zjiecode.com/api/send/message"

    def send(self, content, summary="Quant Alert"):
        if not self.uid:
            logger.warning("No WeChat UID configured. Notification skipped.")
            return False
        
        app_token = os.environ.get("WX_APP_TOKEN")
        if not app_token:
            logger.warning("WX_APP_TOKEN not set in environment variables. Using mock notification.")
            logger.info(f"Mock Notification sent to {self.uid}: {content}")
            return True

        payload = {
            "appToken": app_token,
            "content": content,
            "summary": summary,
            "contentType": 1,
            "topicIds": [],
            "uids": [self.uid],
            "url": os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")
        }
        
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            logger.info(f"Notification sent to {self.uid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
