import akshare as ak
import pandas as pd
from typing import Dict, Any, Optional

def get_latest_price(symbol: str, market: str) -> Optional[float]:
    """
    Get latest price for US, HK, or A-share (SH/SZ) stock.
    Symbol for HK: e.g., '00700'
    Symbol for US: e.g., 'AAPL'
    Symbol for A-share: e.g., '600519' (SH) or '000001' (SZ)
    """
    try:
        if market.upper() == 'HK':
            # Retry mechanism
            for attempt in range(3):
                try:
                    df = ak.stock_hk_spot_em()
                    row = df[df['代码'] == symbol]
                    if not row.empty:
                        return float(row['最新价'].values[0])
                    break 
                except Exception as e:
                    print(f"Attempt {attempt+1} failed for {symbol}: {e}")
                    if attempt == 2: pass # Fallback to None if all fail? Or keep silent for yfinance?
            
            # Fallback to yfinance if akshare failed
            try:
                import yfinance as yf
                clean_symbol = symbol.replace('.HK', '').lstrip('0')
                ticker = f"{clean_symbol.zfill(4)}.HK"
                price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
                return float(price)
            except Exception as e:
                print(f"yfinance fallback failed for {symbol}: {e}")

        elif market.upper() == 'US':
            for attempt in range(3):
                try:
                    df = ak.stock_us_spot_em()
                    row = df[df['代码'] == symbol]
                    if not row.empty:
                        return float(row['最新价'].values[0])
                    break
                except Exception as e:
                    print(f"Attempt {attempt+1} failed for {symbol}: {e}")
            
            # Fallback to yfinance
            try:
                import yfinance as yf
                price = yf.Ticker(symbol).history(period="1d")['Close'].iloc[-1]
                return float(price)
            except Exception as e:
                print(f"yfinance fallback failed for {symbol}: {e}")
        
        elif market.upper() in ['SH', 'SZ']:
            # A股 (China mainland)
            for attempt in range(3):
                try:
                    df = ak.stock_zh_a_spot_em()
                    # 代码格式：600519 或 000001
                    row = df[df['代码'] == symbol]
                    if not row.empty:
                        return float(row['最新价'].values[0])
                    break
                except Exception as e:
                    print(f"Attempt {attempt+1} failed for A-share {symbol}: {e}")
            
            # Fallback to yfinance
            try:
                import yfinance as yf
                # yfinance A股格式：600519.SS (上海) 或 000001.SZ (深圳)
                suffix = '.SS' if market.upper() == 'SH' else '.SZ'
                ticker = f"{symbol}{suffix}"
                price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
                return float(price)
            except Exception as e:
                print(f"yfinance fallback failed for A-share {symbol}: {e}")
                
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None
    return None

def get_stock_history(symbol: str, market: str) -> str:
    """
    Get recent history summary string for analysis.
    """
    try:
        import yfinance as yf
        
        history_df = None
        
        # Try Akshare first (giving it a chance but knowing it's unstable)
        try:
            if market.upper() == 'HK':
                # Akshare HK
                 for attempt in range(3):
                    try:
                        history_df = ak.stock_hk_daily(symbol=symbol, adjust="qfq")
                        if history_df is not None and not history_df.empty:
                            break
                    except:
                        pass
            elif market.upper() == 'US':
                 # Akshare US often unstable for hist, try once
                 try:
                     history_df = ak.stock_us_hist(symbol=symbol)
                 except:
                     pass
            elif market.upper() in ['SH', 'SZ']:
                 # A股历史数据
                 try:
                     history_df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
                     if history_df is not None and not history_df.empty:
                         pass  # success
                 except Exception as e:
                     print(f"Akshare A-share history fetch failed: {e}")

        except Exception as e:
            print(f"Akshare history fetch failed: {e}")

        # Fallback to yfinance if akshare didn't return data
        if history_df is None or history_df.empty:
            print(f"Falling back to yfinance for history: {symbol}")
            ticker = symbol
            if market.upper() == 'HK':
                clean_symbol = symbol.replace('.HK', '').lstrip('0')
                ticker = f"{clean_symbol.zfill(4)}.HK"
            elif market.upper() in ['SH', 'SZ']:
                # yfinance A股格式：600519.SS (上海) 或 000001.SZ (深圳)
                suffix = '.SS' if market.upper() == 'SH' else '.SZ'
                ticker = f"{symbol}{suffix}"
            
            stock = yf.Ticker(ticker)
            # Get 1 month to ensure we have enough for last 5 days
            history_df = stock.history(period="1mo")
            
            # Format yfinance df to string similar to what we want
            if not history_df.empty:
                # Keep only Close, Volume, etc?
                # Just last 5 rows
                recent = history_df.tail(5)
                return recent.to_string()

        if history_df is not None and not history_df.empty:
             recent = history_df.tail(5)
             return recent.to_string()
        
        return "No historical data available."

    except Exception as e:
        return f"Error fetching history: {e}"

def get_money_flow_data(symbol: str, market: str) -> str:
    """
    Get daily money flow data, including overall and main force flows with volume analysis.
    Returns formatted string with money flow analysis data.
    """
    try:
        if market.upper() == 'HK':
            # For HK stocks, try to get money flow data from AKShare
            try:
                clean_symbol = symbol.lstrip('0')
                df = ak.stock_individual_fund_flow_rank(indicator="今日")
                hk_symbol = f"{clean_symbol.zfill(5)}"
                matching_rows = df[df['代码'].astype(str).str.contains(hk_symbol, na=False)]
                
                if not matching_rows.empty:
                    row = matching_rows.iloc[0]
                    result = f"""资金流向数据 (港股):
- 主力净流入: {row.get('主力净流入', 'N/A')}
- 超大单净流入: {row.get('超大单净流入', 'N/A')}
- 大单净流入: {row.get('大单净流入', 'N/A')}
- 中单净流入: {row.get('中单净流入', 'N/A')}
- 小单净流入: {row.get('小单净流入', 'N/A')}
- 主力净占比: {row.get('主力净占比', 'N/A')}
"""
                    return result
            except Exception as e:
                print(f"Error fetching HK money flow from AKShare: {e}")
        
        elif market.upper() in ['SH', 'SZ']:
            # A股资金流向数据
            try:
                df = ak.stock_individual_fund_flow(stock=symbol, market="sh" if market.upper() == 'SH' else "sz")
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    result = f"""资金流向数据 (A股):
- 主力净流入: {latest.get('主力净流入-净额', 'N/A')}
- 超大单净流入: {latest.get('超大单净流入-净额', 'N/A')}
- 大单净流入: {latest.get('大单净流入-净额', 'N/A')}
- 中单净流入: {latest.get('中单净流入-净额', 'N/A')}
- 小单净流入: {latest.get('小单净流入-净额', 'N/A')}
"""
                    return result
            except Exception as e:
                print(f"Error fetching A-share money flow from AKShare: {e}")
                
        # Fallback: Use volume-based analysis for all markets
        try:
            import yfinance as yf
            ticker_symbol = symbol
            if market.upper() == 'HK':
                clean_symbol = symbol.replace('.HK', '').lstrip('0')
                ticker_symbol = f"{clean_symbol.zfill(4)}.HK"
            elif market.upper() in ['SH', 'SZ']:
                # yfinance A股格式
                suffix = '.SS' if market.upper() == 'SH' else '.SZ'
                ticker_symbol = f"{symbol}{suffix}"
            
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                recent = hist.tail(5)
                volume_analysis = []
                
                for idx, (date, row) in enumerate(recent.iterrows()):
                    volume_change = ""
                    if idx > 0:
                        prev_volume = recent.iloc[idx-1]['Volume']
                        curr_volume = row['Volume']
                        change_pct = ((curr_volume - prev_volume) / prev_volume * 100) if prev_volume > 0 else 0
                        volume_change = f" (较前日{'+' if change_pct > 0 else ''}{change_pct:.1f}%)"
                    
                    price_change = row['Close'] - row['Open']
                    price_direction = "上涨" if price_change > 0 else "下跌" if price_change < 0 else "平盘"
                    
                    volume_analysis.append(
                        f"- {date.strftime('%Y-%m-%d')}: 成交量 {int(row['Volume']):,}{volume_change}, "
                        f"价格{price_direction} ({row['Close']:.2f})"
                    )
                
                market_labels = {'HK': '港股', 'US': '美股', 'SH': 'A股沪市', 'SZ': 'A股深市'}
                market_label = market_labels.get(market.upper(), market)
                result = f"""资金流向数据 ({market_label} - 基于成交量分析):
{chr(10).join(volume_analysis)}

注: 数据基于成交量变化分析，结合价格走势判断资金流向趋势。
"""
                return result
        except Exception as e:
            print(f"Error fetching volume data: {e}")
            
        return "资金流向数据暂时无法获取，将基于历史价格进行综合分析。"
                
    except Exception as e:
        print(f"Error in get_money_flow_data: {e}")
        return "资金流向数据获取失败，将基于历史价格和成交量进行综合分析。"

# Caching for stock names
_cache_hk_df = None
_cache_us_df = None
_cache_hk_time = 0
_cache_us_time = 0

import time

def get_sina_stock_name(symbol: str, market: str) -> Optional[str]:
    """
    Fallback to Sina Finance for Chinese names.
    """
    try:
        import requests
        import re
        if market.upper() == 'HK':
            s_symbol = f"hk{symbol.lstrip('0').zfill(5)}"
        elif market.upper() == 'US':
            s_symbol = f"gb_{symbol.lower()}"
        else:
            return None
            
        url = f"http://hq.sinajs.cn/list={s_symbol}"
        headers = {
            "Referer": "http://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            content = res.content.decode('gbk', errors='ignore')
            match = re.search(r'="([^,"]+)', content)
            if match:
                name = match.group(1).strip()
                if name and name != "FAILED" and not name.isdigit():
                    return name
    except Exception as e:
        print(f"Sina fallback failed for {symbol}: {e}")
    return None

_cache_ts_hk_df = None
_cache_ts_us_df = None
_cache_ts_hk_time = 0
_cache_ts_us_time = 0

TUSHARE_TOKEN = "8308ccd2d6166e49e53836ed323384ba9d85f259798b6a928c91ca01"

def get_tushare_stock_name(symbol: str, market: str) -> Optional[str]:
    """
    Fetch Chinese stock name from Tushare.
    """
    import time
    global _cache_ts_hk_df, _cache_ts_us_df, _cache_ts_hk_time, _cache_ts_us_time
    now = time.time()
    CACHE_EXPIRY = 86400 # 24 hours for basic info
    
    try:
        import tushare as ts
        pro = ts.pro_api(TUSHARE_TOKEN)
        if market.upper() == 'HK':
            if _cache_ts_hk_df is None or (now - _cache_ts_hk_time) > CACHE_EXPIRY:
                _cache_ts_hk_df = pro.hk_basic()
                _cache_ts_hk_time = now
            if _cache_ts_hk_df is not None:
                # HK symbols in tushare are often '00700'
                lookup = symbol.lstrip('0').zfill(5)
                row = _cache_ts_hk_df[_cache_ts_hk_df['symbol'] == lookup]
                if not row.empty:
                    return row['name'].values[0]
                    
        elif market.upper() == 'US':
            if _cache_ts_us_df is None or (now - _cache_ts_us_time) > CACHE_EXPIRY:
                _cache_ts_us_df = pro.us_basic()
                _cache_ts_us_time = now
            if _cache_ts_us_df is not None:
                lookup = symbol.upper()
                row = _cache_ts_us_df[_cache_ts_us_df['symbol'] == lookup]
                if not row.empty:
                    return row['name'].values[0]
    except Exception as e:
        print(f"Tushare fetch failed for {symbol}: {e}")
    return None

def get_tencent_stock_name(symbol: str, market: str) -> Optional[str]:
    """
    Fallback to Tencent Finance for Chinese names.
    """
    try:
        import requests
        if market.upper() == 'HK':
            t_symbol = f"hk{symbol.lstrip('0').zfill(5)}"
        elif market.upper() == 'US':
            t_symbol = f"us{symbol.upper()}"
        else:
            return None
            
        url = f"http://qt.gtimg.cn/q={t_symbol}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            content = res.text
            # Format: v_hk00700="200~腾讯控股~00700~...~";
            parts = content.split('~')
            if len(parts) > 1:
                name = parts[1].strip()
                if name and not name.isdigit():
                    return name
    except Exception as e:
        print(f"Tencent fallback failed for {symbol}: {e}")
    return None

def get_stock_name(symbol: str, market: str) -> str:
    """
    Try to fetch stock name via akshare/Sina/Tencent for Chinese names, 
    then yfinance as last resort.
    """
    global _cache_hk_df, _cache_us_df, _cache_hk_time, _cache_us_time
    now = time.time()
    CACHE_EXPIRY = 3600 # 1 hour

    try:
        # 1. Try Tushare (Primary source for Chinese names)
        ts_name = get_tushare_stock_name(symbol, market)
        if ts_name:
            return ts_name

        # 2. Try Tencent Finance (Chinese fallback, generally better for HK)
        tencent_name = get_tencent_stock_name(symbol, market)
        if tencent_name:
            return tencent_name

        # 3. Try Sina Finance (Chinese fallback)
        sina_name = get_sina_stock_name(symbol, market)
        if sina_name:
            return sina_name

        # 4. Fallback to yfinance (Usually English)
        try:
            import yfinance as yf
            ticker_symbol = symbol
            if market.upper() == 'HK':
                clean_symbol = symbol.replace('.HK', '').lstrip('0')
                ticker_symbol = f"{clean_symbol.zfill(4)}.HK"
            elif market.upper() in ['SH', 'SZ']:
                # yfinance A股格式：600519.SS (上海) 或 000001.SZ (深圳)
                suffix = '.SS' if market.upper() == 'SH' else '.SZ'
                ticker_symbol = f"{symbol}{suffix}"
            
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            name = info.get('shortName') or info.get('longName')
            if name:
                return name
        except Exception as ey:
            print(f"yfinance fallback failed for {symbol}: {ey}")
            
        return symbol
    except Exception as e:
        print(f"Error fetching name for {symbol}: {e}")
        return symbol

def get_intraday_chart(symbol: str, market: str) -> list:
    """
    Get intraday chart data (last 1 day, 5m or 15m interval)
    Returns list of {'time': str, 'price': float}
    """
    try:
        # 1. Try Tencent Finance (More stable for deployment environments)
        import requests
        
        qt_symbol = symbol
        if market.upper() == 'HK':
            # 00700 -> hk00700
            qt_symbol = f"hk{symbol.lstrip('0').zfill(5)}"
        elif market.upper() == 'US':
            # AAPL -> usAAPL
            qt_symbol = f"us{symbol.upper()}"
        elif market.upper() == 'SH':
            # 600519 -> sh600519
            qt_symbol = f"sh{symbol}"
        elif market.upper() == 'SZ':
            # 000001 -> sz000001
            qt_symbol = f"sz{symbol}"
            
        # Tencent Minute Data API
        url = f"http://web.ifzq.gtimg.cn/appstock/app/minute/query?code={qt_symbol}"
        res = requests.get(url, timeout=3)
        
        chart_data = []
        if res.status_code == 200:
            data = res.json()
            # Navigate path: data -> [symbol] -> data -> data
            # Response structure: {"data": {"hk00700": {"data": {"data": ["0930 380.20 100 ..."]}}}}
            if 'data' in data and qt_symbol in data['data']:
                inner_data = data['data'][qt_symbol].get('data', {}).get('data', [])
                
                # Sample logic: Tencent returns 1-min data (Format: "HHMM PRICE VOLUME...")
                # We want to downsample to ~15min or similar to reduce points, or just return all?
                # Frontend handles path fine regardless of count usually.
                # Let's return all points but format time.
                
                for point in inner_data:
                    parts = point.split(' ')
                    if len(parts) >= 2:
                        raw_time = parts[0] # "0930"
                        price = float(parts[1])
                        
                        # Format HH:MM
                        formatted_time = f"{raw_time[:2]}:{raw_time[2:]}"
                        
                        chart_data.append({
                            "time": formatted_time,
                            "price": price
                        })
                
                # If we got data, return it. If empty (e.g. pre-market and no data?), fallback.
                if chart_data:
                    # Optional: Downsample if too many points? 
                    # Tencent gives ALL minutes. That's ~330 points. 
                    # Let's take every 5th point to mimic 5m interval roughly
                    return chart_data[::5]

        # 2. Fallback to yfinance
        import yfinance as yf
        ticker_symbol = symbol
        if market.upper() == 'HK':
             # Normalize HK symbol: 00700 -> 0700.HK
             clean_symbol = symbol.replace('.HK', '').lstrip('0')
             ticker_symbol = f"{clean_symbol.zfill(4)}.HK"
             
        ticker = yf.Ticker(ticker_symbol)
        # Get 1 day data with 5m interval
        hist = ticker.history(period="1d", interval="15m")
        
        if hist.empty:
            # Fallback to 5d history if 1d is empty
            hist = ticker.history(period="5d", interval="60m")
            
        for index, row in hist.iterrows():
            # Format index to string HH:MM
            time_str = index.strftime("%H:%M") if hasattr(index, 'strftime') else str(index)
            if len(hist) > 50: 
                 time_str = index.strftime("%m-%d %H:%M")
                 
            chart_data.append({
                "time": time_str,
                "price": float(row['Close'])
            })
        return chart_data
    except Exception as e:
        print(f"Error fetching chart: {e}")
        return []
