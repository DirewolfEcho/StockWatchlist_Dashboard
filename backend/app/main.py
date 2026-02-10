from fastapi import FastAPI, HTTPException, Body, Header, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
import json
import os
from datetime import datetime
from app.models import Stock, StockBase, AppState, AnalysisReport, TimerSettings, UserProfile
from app.services.analysis import generate_stock_report
from app.services.scheduler import start_scheduler, set_daily_job
import threading

app = FastAPI()

# CORS config allowing frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity in deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "data.json"

# Import database service
from app.services.database import (
    save_app_state_to_db, 
    load_app_state_from_db, 
    is_supabase_configured
)

# In-memory retrieval with persistence (Supabase or local file)
def load_data() -> AppState:
    """Load app state from Supabase first, then fallback to local file."""
    
    # Try Supabase first
    if is_supabase_configured():
        db_data = load_app_state_from_db()
        if db_data:
            try:
                data = json.loads(db_data)
                # Parse datetimes
                data = parse_datetimes(data)
                print("✅ Loaded data from Supabase")
                return AppState(**data)
            except Exception as e:
                print(f"Error parsing Supabase data: {e}")
    
    # Fallback to local file
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
                data = parse_datetimes(data)
                print("📁 Loaded data from local file")
                return AppState(**data)
            except Exception as e:
                print(f"Error loading local data: {e}")
                return AppState()
    
    return AppState()

def parse_datetimes(data: dict) -> dict:
    """Parse datetime strings back to datetime objects."""
    # Global Watchlist
    for stock in data.get("watchlist", []):
        if isinstance(stock.get("added_at"), str):
            stock["added_at"] = datetime.fromisoformat(stock["added_at"])
    
    # Users Watchlists and Reports
    if "users" in data and isinstance(data["users"], dict):
        for email, profile in data["users"].items():
            if "watchlist" in profile:
                for stock in profile["watchlist"]:
                    if isinstance(stock.get("added_at"), str):
                        stock["added_at"] = datetime.fromisoformat(stock["added_at"])
            if "reports" in profile:
                for report in profile["reports"]:
                    if isinstance(report.get("generated_at"), str):
                        report["generated_at"] = datetime.fromisoformat(report["generated_at"])
    
    # Global Reports
    for report in data.get("reports", []):
        if isinstance(report.get("generated_at"), str):
            report["generated_at"] = datetime.fromisoformat(report["generated_at"])
    
    return data

def save_data(state: AppState):
    """Save app state to both Supabase and local file."""
    state_json = state.model_dump_json()
    
    # Save to Supabase if configured
    if is_supabase_configured():
        if save_app_state_to_db(state_json):
            print("✅ Saved to Supabase")
        else:
            print("⚠️ Supabase save failed, using local file only")
    
    # Always save to local file as backup
    with open(DATA_FILE, "w") as f:
        f.write(state_json)

app_state = load_data()

# Helper to get the correct watchlist
def get_user_watchlist_ref(app_state: AppState, user_email: Optional[str]) -> List[Stock]:
    if user_email:
        if user_email not in app_state.users:
            app_state.users[user_email] = UserProfile()
        return app_state.users[user_email].watchlist
    else:
        # Return empty list for guests to ensure isolation (frontend handles local storage)
        return []

# --- Job Function ---
def run_analysis_job():
    import time as job_time
    print("Running analysis job...")
    from datetime import timedelta
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Process each user's watchlist separately
    for user_email, user_profile in app_state.users.items():
        print(f"Processing user: {user_email}")
        
        for i, stock in enumerate(user_profile.watchlist):
            print(f"  [{i+1}/{len(user_profile.watchlist)}] Analyzing {stock.symbol} for {user_email}...")
            try:
                report = generate_stock_report(stock.symbol, stock.market)
                report.user_id = user_email
                
                # Remove existing report for this stock from today for this user
                user_profile.reports = [
                    r for r in user_profile.reports 
                    if not (r.stock_symbol == stock.symbol and r.generated_at.date() == today)
                ]
                
                # Add new report to user's reports
                user_profile.reports.insert(0, report)
                print(f"  ✅ Report generated for {stock.symbol}")
                
                # Save after each report to prevent data loss  
                save_data(app_state)
                
            except Exception as e:
                print(f"  ❌ Analysis failed for {stock.symbol}: {e}")
            
            # Brief delay between stocks to avoid API rate limits
            if i < len(user_profile.watchlist) - 1:
                job_time.sleep(3)
        
        # Clean up: only keep reports from today and yesterday for this user
        user_profile.reports = [
            r for r in user_profile.reports
            if r.generated_at.date() >= yesterday
        ]
    
    # Also process guest/global watchlist (legacy support)
    for i, stock in enumerate(app_state.watchlist):
        print(f"Analyzing {stock.symbol} (guest)...")
        try:
            report = generate_stock_report(stock.symbol, stock.market)
            report.user_id = None  # Guest report
            
            # Remove existing report for this stock from today
            app_state.reports = [
                r for r in app_state.reports 
                if not (r.stock_symbol == stock.symbol and r.generated_at.date() == today)
            ]
            
            # Add new report
            app_state.reports.insert(0, report)
            save_data(app_state)
        except Exception as e:
            print(f"Analysis failed for {stock.symbol}: {e}")
        
        if i < len(app_state.watchlist) - 1:
            job_time.sleep(3)
    
    # Clean up global reports
    app_state.reports = [
        r for r in app_state.reports
        if r.generated_at.date() >= yesterday
    ]
    
    save_data(app_state)
    print("✅ Analysis job finished.")

# --- Routes ---

@app.on_event("startup")
def startup_event():
    start_scheduler()
    if app_state.timer:
        set_daily_job(run_analysis_job, app_state.timer)

@app.get("/")
def read_root():
    return {"message": "Stock Analyzer API is running"}

@app.get("/stocks", response_model=List[Stock])
def get_watchlist(response: Response, x_user_email: Optional[str] = Header(None), user_email: Optional[str] = Query(None)):
    # Reload data to ensure freshness in multi-worker env
    global app_state
    app_state = load_data()
    
    final_email = x_user_email or user_email
    response.headers["X-Debug-User"] = str(final_email)
    
    print(f"GET /stocks - User identifier: {final_email}")
    result = get_user_watchlist_ref(app_state, final_email)
    print(f"GET /stocks - Returning {len(result)} stocks for user: {final_email}")
    
    return result

@app.post("/stocks", response_model=Stock)
def add_stock(response: Response, stock_base: StockBase, x_user_email: Optional[str] = Header(None), user_email: Optional[str] = Query(None)):
    global app_state
    app_state = load_data()
    
    final_email = x_user_email or user_email
    response.headers["X-Debug-User"] = str(final_email)
    
    print(f"POST /stocks - User identifier: {final_email}, Symbol: {stock_base.symbol}")
    
    if not final_email:
        print("ERROR: No user identifier provided!")
        raise HTTPException(status_code=401, detail="需要登录才能添加股票")
    
    target_list = get_user_watchlist_ref(app_state, final_email)
    print(f"POST /stocks - Current watchlist size for {final_email}: {len(target_list)}")


    
    symbol = stock_base.symbol.strip().upper()
    market = stock_base.market.upper()
    
    # Normalize HK symbol: 700 -> 00700, 0700 -> 00700
    if market == 'HK':
        clean = symbol.replace('.HK', '').lstrip('0')
        symbol = clean.zfill(5)
    
    # Check duplicates with normalized logic within TARGET list
    for s in target_list:
        s_symbol = s.symbol.upper()
        if s.market == 'HK':
             s_symbol = s.symbol.lstrip('0').zfill(5)
        
        target_symbol = symbol 
             
        if s_symbol == target_symbol and s.market == market:
            raise HTTPException(status_code=400, detail="该股票已在关注列表中")
            
    fetched_name = stock_base.name
    if not fetched_name:
        from app.services.stock_data import get_stock_name
        fetched_name = get_stock_name(symbol, market)

    new_stock = Stock(
        symbol=symbol, 
        market=market, 
        name=fetched_name, 
        added_at=datetime.now()
    )
    
    target_list.append(new_stock)
    print(f"POST /stocks - Stock appended. New watchlist size: {len(target_list)}")
    
    save_data(app_state)
    print(f"POST /stocks - Data saved. Returning stock: {new_stock.symbol}")
    
    return new_stock

@app.get("/stocks/{market}/{symbol}/chart")
def get_chart(market: str, symbol: str):
    """Get intraday chart data for a stock"""
    from app.services.stock_data import get_intraday_chart
    try:
        chart_data = get_intraday_chart(symbol, market)
        return chart_data
    except Exception as e:
        print(f"Error getting chart for {symbol} ({market}): {e}")
        return []

@app.delete("/stocks/{symbol}")
def remove_stock(symbol: str, x_user_email: Optional[str] = Header(None), user_email: Optional[str] = Query(None)):
    final_email = x_user_email or user_email
    target_list = get_user_watchlist_ref(app_state, final_email)
    
    symbol_upper = symbol.upper()
    
    # Find index to remove
    to_remove_idx = -1
    for i, s in enumerate(target_list):
        if s.symbol.upper() == symbol_upper:
            to_remove_idx = i
            break
            
    if to_remove_idx != -1:
        target_list.pop(to_remove_idx)
        save_data(app_state)
        
    return {"status": "removed"}


@app.get("/reports", response_model=List[AnalysisReport])
def get_reports(date_filter: str = "today", user_email: Optional[str] = None):
    """
    Get reports filtered by date and user.
    date_filter: 'today', 'yesterday', or 'all'
    user_email: User email to filter reports for (if None, returns guest reports)
    """
    from datetime import timedelta
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Get user-specific reports if user_email provided
    if user_email and user_email in app_state.users:
        user_reports = app_state.users[user_email].reports
    else:
        # Return global/guest reports for non-logged-in users
        user_reports = app_state.reports
    
    if date_filter == "today":
        filtered = [r for r in user_reports if r.generated_at.date() == today]
    elif date_filter == "yesterday":
        filtered = [r for r in user_reports if r.generated_at.date() == yesterday]
    else:  # 'all'
        filtered = user_reports
    
    # Return sorted by date desc
    return sorted(filtered, key=lambda x: x.generated_at, reverse=True)

@app.post("/settings/timer")
def set_timer(settings: TimerSettings):
    app_state.timer = settings.time
    set_daily_job(run_analysis_job, settings.time)
    save_data(app_state)
    return {"status": "updated", "time": settings.time}

@app.post("/debug/trigger-analysis")
def trigger_analysis():
    # Run in background thread to not block response
    thread = threading.Thread(target=run_analysis_job)
    thread.start()
    return {"message": "Analysis started in background"}
