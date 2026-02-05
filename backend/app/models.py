from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class StockBase(BaseModel):
    symbol: str
    market: str  # 'US' or 'HK'
    name: Optional[str] = None

class Stock(StockBase):
    added_at: datetime

class TimerSettings(BaseModel):
    time: str  # Format "HH:MM" 24h format

class NewsItem(BaseModel):
    title: str
    content: str
    sentiment: Optional[str] = '中性'  # '正面', '负面', '中性'

class AnalysisReport(BaseModel):
    stock_symbol: str
    stock_name: Optional[str] = None
    report_content: str
    generated_at: datetime
    price: Optional[float] = None
    recommendation: Optional[str] = None # 'BUY', 'SELL', 'HOLD'
    news_items: List['NewsItem'] = []
    user_id: Optional[str] = None  # User who owns this report

# For persisting data simply in this MVP
class UserProfile(BaseModel):
    watchlist: List[Stock] = []
    reports: List[AnalysisReport] = []  # User-specific reports

class AppState(BaseModel):
    # Global/Guest watchlist (legacy support)
    watchlist: List[Stock] = []
    
    # User specific data: email -> profile
    users: Dict[str, UserProfile] = {}
    
    timer: Optional[str] = "09:00"
    # Keep global reports for backward compatibility, but prefer user-specific
    reports: List[AnalysisReport] = []
