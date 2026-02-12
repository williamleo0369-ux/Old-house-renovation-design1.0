from apscheduler.schedulers.background import BackgroundScheduler
from quant_engine import GridStrategy
import logging
from feishu_integration import push_to_feishu_bitable

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
strategies = {}

def run_strategy(strategy_id):
    if strategy_id in strategies:
        result = strategies[strategy_id].run()
        logger.info(f"Strategy {strategy_id} run result: {result}")

def add_strategy(symbol, upper, lower, uid):
    strategy_id = f"{symbol}_{uid}"
    strategy = GridStrategy(symbol, upper, lower)
    strategy.notifier.uid = uid # Set the user ID
    strategies[strategy_id] = strategy
    
    # Add job to scheduler if not exists
    if not scheduler.get_job(strategy_id):
        # Check every 20 seconds for near-real-time monitoring
        scheduler.add_job(run_strategy, 'interval', seconds=20, args=[strategy_id], id=strategy_id)
        logger.info(f"Added strategy job: {strategy_id}")
    
    return strategy_id

def get_all_strategies_status():
    status_list = []
    for sid, strategy in strategies.items():
        status = strategy.get_status()
        status['id'] = sid
        status_list.append(status)
    return status_list

def start_scheduler():
    if not scheduler.running:
        # Existing Grid Strategy Jobs
        # (Managed dynamically by add_strategy)
        
        # New Feature: Daily Feishu Report at 15:05 Mon-Fri
        scheduler.add_job(
            push_to_feishu_bitable, 
            'cron', 
            day_of_week='mon-fri', 
            hour=15, 
            minute=5, 
            id='feishu_daily_report',
            replace_existing=True
        )
        logger.info("Added daily Feishu report job (15:05 Mon-Fri)")

        scheduler.start()
        logger.info("Scheduler started")
