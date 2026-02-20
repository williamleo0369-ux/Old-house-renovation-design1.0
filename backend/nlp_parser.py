# backend/nlp_parser.py

import re

def parse_nlp_query(query: str) -> dict:
    """
    Parses a natural language query to extract stock screening rules.
    A simple implementation based on regex and keywords.
    """
    rules = {}
    
    # --- Market Cap --- (e.g., "市值50亿以下", "市值大于100亿")
    market_cap_patterns = [
        r"市值(?:小于|低于|不超过|不高于|<=|<)(\d+\.?\d*)[亿]",
        r"市值(?:大于|高于|不低于|>=|>)(\d+\.?\d*)[亿]",
    ]
    
    # Max market cap
    match = re.search(market_cap_patterns[0], query)
    if match:
        rules['market_cap_max'] = float(match.group(1))
        
    # Min market cap
    match = re.search(market_cap_patterns[1], query)
    if match:
        rules['market_cap_min'] = float(match.group(1))

    # --- PE Ratio --- (e.g., "PE小于15", "市盈率高于10倍")
    pe_patterns = [
        r"(?:PE|市盈率)(?:小于|低于|<=|<)(\d+\.?\d*)",
        r"(?:PE|市盈率)(?:大于|高于|>=|>)(\d+\.?\d*)",
    ]
    
    # Max PE
    match = re.search(pe_patterns[0], query)
    if match:
        rules['pe_ratio_max'] = float(match.group(1))
        
    # Min PE
    match = re.search(pe_patterns[1], query)
    if match:
        rules['pe_ratio_min'] = float(match.group(1))
        
    # --- ROE --- (e.g., "ROE大于15%", "净资产收益率不低于10个点")
    roe_patterns = [
        r"(?:ROE|净资产收益率)(?:大于|高于|>=|>)(\d+\.?\d*)",
    ]
    
    match = re.search(roe_patterns[0], query)
    if match:
        rules['roe_min'] = float(match.group(1))

    # --- Industry/Sector (placeholder) ---
    # A real implementation would need a mapping of keywords to industry codes
    if "医疗美容" in query or "医美" in query:
        # This is a placeholder. We are not actually filtering by industry yet.
        print("Industry keyword '医疗美容' detected, but not yet implemented.")

    return {"custom_rules": rules}
