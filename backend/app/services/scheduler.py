import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import List, Callable

scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()

def set_daily_job(job_func: Callable, run_time: str):
    """
    Set the daily job to run at HH:MM
    """
    # Remove existing job if any
    scheduler.remove_all_jobs()
    
    hour, minute = run_time.split(":")
    
    # Add new job
    scheduler.add_job(
        job_func,
        trigger=CronTrigger(hour=int(hour), minute=int(minute)),
        id="daily_analysis",
        replace_existing=True
    )
    print(f"Job set for {run_time}")

def stop_scheduler():
    scheduler.shutdown()
