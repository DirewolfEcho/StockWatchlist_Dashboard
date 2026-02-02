from fastapi import FastAPI, HTTPException, Body, Header, Query

# ... (rest of imports)

# ... (app setup)

# ... (get_user_watchlist_ref)

# --- Routes ---

# ... (startup)

# ... (root)

@app.get("/stocks", response_model=List[Stock])
def get_watchlist(x_user_email: Optional[str] = Header(None), user_email: Optional[str] = Query(None)):
    final_email = x_user_email or user_email
    return get_user_watchlist_ref(app_state, final_email)

@app.post("/stocks", response_model=Stock)
def add_stock(stock_base: StockBase, x_user_email: Optional[str] = Header(None), user_email: Optional[str] = Query(None)):
    final_email = x_user_email or user_email
    target_list = get_user_watchlist_ref(app_state, final_email)
    
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
    save_data(app_state)
    return new_stock

# ... (get_chart)

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
def get_reports(date_filter: str = "today"):
    """
    Get reports filtered by date.
    date_filter: 'today', 'yesterday', or 'all'
    """
    from datetime import timedelta
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    if date_filter == "today":
        filtered = [r for r in app_state.reports if r.generated_at.date() == today]
    elif date_filter == "yesterday":
        filtered = [r for r in app_state.reports if r.generated_at.date() == yesterday]
    else:  # 'all'
        filtered = app_state.reports
    
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
