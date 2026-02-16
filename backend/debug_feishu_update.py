
import logging
from feishu_integration import FeishuIntegrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_update():
    integrator = FeishuIntegrator()

    print("--- Step 1: Loading all records to get a record_id to test with ---")
    symbols = integrator.load_favorites_from_feishu()
    if not symbols:
        print("No symbols found in Feishu. Cannot proceed with update test.")
        return

    # Get the first symbol and its record_id from the internal map
    try:
        target_symbol = list(integrator._record_id_map.keys())[0]
        target_record_id = integrator._record_id_map[target_symbol]
        print(f"--- Step 2: Found a record to test. Symbol: {target_symbol}, Record ID: {target_record_id} ---")
    except (IndexError, KeyError) as e:
        print(f"Could not get a target record from the integrator's internal map: {e}")
        return

    print("--- Step 3: Attempting to update the record with a new name... ---")
    
    # We will append " [TEST]" to the existing name
    # First, we need to find the current name. Let's just construct a new one.
    new_name_value = f"TEST UPDATE ({target_symbol})"
    
    fields_to_update = {
        "股票代码和名称": new_name_value
    }

    integrator.update_record(target_record_id, fields_to_update)

    print("--- Step 4: Debug script finished. Check logs for success or failure. ---")

if __name__ == "__main__":
    debug_update()
