
import os
import sys
# Add current directory to path so we can import modules
sys.path.append(os.getcwd())

from feishu_integration import feishu_integrator
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

print("Testing Feishu Load...")
try:
    symbols = feishu_integrator.load_favorites_from_feishu()
    print(f"Loaded symbols: {symbols}")
    
    if not symbols:
        print("WARNING: No symbols loaded. Check your Feishu table and permissions.")
    else:
        print(f"SUCCESS: Loaded {len(symbols)} symbols.")
        
except Exception as e:
    print(f"ERROR: {e}")
