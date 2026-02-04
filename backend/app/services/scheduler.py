import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import List, Callable
import pytz

# 使用香港时区 (UTC+8)，适用于港股和A股交易时间
TIMEZONE = pytz.timezone('Asia/Hong_Kong')

scheduler = BackgroundScheduler(timezone=TIMEZONE)

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        print(f"Scheduler started with timezone: {TIMEZONE}")

def set_daily_job(job_func: Callable, run_time: str):
    """
    Set the daily job to run at HH:MM in Hong Kong timezone (UTC+8)
    """
    # Remove existing job if any
    scheduler.remove_all_jobs()
    
    hour, minute = run_time.split(":")
    
    # Add new job with timezone
    scheduler.add_job(
        job_func,
        trigger=CronTrigger(hour=int(hour), minute=int(minute), timezone=TIMEZONE),
        id="daily_analysis",
        replace_existing=True
    )
    
    # Get next run time for logging
    job = scheduler.get_job("daily_analysis")
    next_run = job.next_run_time if job else "Unknown"
    print(f"Job set for {run_time} (Hong Kong time). Next run: {next_run}")

def stop_scheduler():
    scheduler.shutdown()
