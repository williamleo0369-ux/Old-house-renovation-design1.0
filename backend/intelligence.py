# backend/intelligence.py

import requests
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

CLS_API_URL = "https://api.98dou.cn/api/hotlist/cls/all"
XUEQIU_COMMENTS_URL = "https://xueqiu.com/query/v1/comments.json"

# --- Cailianpress Functions ---

def get_cls_telegraphs():
    """
    Fetches the latest telegraphs from Cailianpress.
    """
    try:
        response = requests.get(CLS_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 200 and data.get("data"):
            logger.info(f"Successfully fetched {len(data['data'])} articles from Cailianpress.")
            return data["data"]
        else:
            logger.warning(f"Cailianpress API returned non-200 or empty data: {data}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from Cailianpress: {e}")
        return []

def analyze_cls_for_symbol(symbol_keywords: list, institutional_keywords: list):
    """
    Analyzes Cailianpress telegraphs for a given symbol and extracts institutional logic.
    """
    telegraphs = get_cls_telegraphs()
    today_str = datetime.now().strftime('%Y-%m-%d')
    relevant_summaries = []

    for telegraph in telegraphs:
        if not telegraph.get('time', '').startswith(today_str):
            continue
        content = telegraph.get('content', '')
        if any(keyword in content for keyword in symbol_keywords):
            found_keywords = [kw for kw in institutional_keywords if kw in content]
            if found_keywords:
                summary = f"【财联社】{telegraph.get('title')} (关键词: {', '.join(found_keywords)})"
                relevant_summaries.append(summary)
    return relevant_summaries

# --- Xueqiu Functions ---

def get_xueqiu_comments(symbol: str, count: int = 20):
    """
    Fetches comments for a specific stock symbol from Xueqiu.
    Note: Xueqiu has anti-scraping measures. This requires setting a browser-like User-Agent
    and potentially cookies to work reliably.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }
    params = {
        'symbol': symbol,
        'count': count,
        'page': 1,
        'comment': 'true',
        'hl': 'false'
    }
    try:
        # Xueqiu requires a cookie to be set. We'll try without it first, but it will likely fail.
        # A more robust solution would involve managing a session or passing a valid cookie.
        # For this example, we will simulate a request that might be blocked.
        response = requests.get(XUEQIU_COMMENTS_URL, headers=headers, params=params, timeout=10)
        
        # A successful request might still be a login page if cookies are missing.
        if "雪球" not in response.text:
             logger.warning("Failed to fetch from Xueqiu, likely due to missing authentication. Response was not a valid JSON.")
             return []

        response.raise_for_status()
        data = response.json()
        comments = data.get('comments', [])
        logger.info(f"Successfully fetched {len(comments)} comments from Xueqiu for {symbol}.")
        return comments
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(f"Error fetching or parsing data from Xueqiu for {symbol}: {e}")
        logger.info("This is common if you are not providing a valid cookie in the request header.")
        return []

def analyze_xueqiu_sentiment(comments: list):
    """
    Performs simple sentiment analysis on a list of Xueqiu comments.
    """
    sentiment_dict = {
        '极度恐慌（买点近）': ['跌停', '救命', '崩盘', '完蛋', '割肉'],
        '过度乐观（卖点近）': ['牛市', '梭哈', '起飞', '发财', '无脑买']
    }
    
    panic_score = 0
    optimism_score = 0
    
    for comment in comments:
        text = comment.get('text', '')
        for word in sentiment_dict['极度恐慌（买点近）']:
            if word in text:
                panic_score += 1
        for word in sentiment_dict['过度乐观（卖点近）']:
            if word in text:
                optimism_score += 1

    # Simple logic to determine overall sentiment
    if panic_score > optimism_score and panic_score > 2: # Require a minimum number of mentions
        return '极度恐慌（买点近）'
    if optimism_score > panic_score and optimism_score > 2:
        return '过度乐观（卖点近）'
    
    return '中性'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # --- Test Cailianpress ---
    cls_symbol_keywords = ['中证1000', '512100']
    cls_institutional_keywords = ['增量资金', '净流入', '减仓', '加仓', '资金流出']
    cls_summaries = analyze_cls_for_symbol(cls_symbol_keywords, cls_institutional_keywords)
    
    print("--- Cailianpress Institutional Logic Summary ---")
    if cls_summaries:
        for summary in cls_summaries:
            print(summary)
    else:
        print("No relevant institutional logic found for the given keywords today.")
    print("---------------------------------------------")

    # --- Test Xueqiu ---
    xueqiu_symbol = 'SH512100' # Xueqiu uses SH/SZ prefix
    comments = get_xueqiu_comments(xueqiu_symbol)
    
    print(f"\n--- Xueqiu Sentiment Analysis for {xueqiu_symbol} ---")
    if comments:
        sentiment = analyze_xueqiu_sentiment(comments)
        print(f"Overall Sentiment: {sentiment}")
        print("\nSample Comments:")
        for i, comment in enumerate(comments[:5]): # Print top 5
            print(f"{i+1}. {comment.get('text')}")
    else:
        print("Could not retrieve comments from Xueqiu. This might be due to API restrictions.")
    print("---------------------------------------------")
