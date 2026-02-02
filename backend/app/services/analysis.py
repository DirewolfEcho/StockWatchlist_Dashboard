import google.generativeai as genai
from .stock_data import get_latest_price, get_stock_history, get_stock_name
from .news_data import get_stock_news
from ..models import AnalysisReport
from datetime import datetime

# Initialize client if key exists
GEMINI_API_KEY = "AIzaSyCX11m_RJxcifuksECiB_krrf8IkntGQiQ"
genai.configure(api_key=GEMINI_API_KEY)


def generate_stock_report(symbol: str, market: str) -> AnalysisReport:
    # 1. Fetch Data
    current_price = get_latest_price(symbol, market)
    history_str = get_stock_history(symbol, market)
    stock_name = get_stock_name(symbol, market)
    
    # Fetch money flow data
    from .stock_data import get_money_flow_data
    money_flow_data = get_money_flow_data(symbol, market)
    
    # Fetch news items
    from .news_data import get_stock_news, get_stock_news_summary
    
    # Create price context for checking
    price_context = {'price': current_price} if current_price else None
    
    news_items = get_stock_news(symbol, market, price_context=price_context)
    news_str = get_stock_news_summary(symbol, market)
    
    # 2. Construct Prompt
    prompt = f"""
    请分析以下股票: {stock_name} ({symbol}, {market}市场)。
    
    数据:
    当前价格: {current_price if current_price else 'N/A'}
    
    最近5日历史数据: 
    {history_str}
    
    资金流向数据:
    {money_flow_data}
    
    最近相关新闻:
    {news_str}
    
    请根据以上数据，提供一份专业的简体中文分析报告。务必包含以下部分：
    1. 资金流向分析 (重点分析主力资金与散户资金的流向，结合成交量变化趋势)
    2. 技术指标分析 (趋势、支撑位、阻力位)
    3. 明确的买入和卖出参考点位建议
    
    请严格按照以下 JSON 格式返回，不要包含 markdown 格式（如 ```json ... ```）。只需返回原始 JSON 字符串。

    {{
      "recommendation": "BUY" | "SELL" | "HOLD",
      "risk_level": "High" | "Medium" | "Low",
      "summary": "一句简短的核心观点总结。",
      "technical_analysis": "详细的技术指标分析。",
      "money_flow": "资金流向详细分析，重点区分主力资金和散户资金的流向，结合成交量数据进行深入分析。",
      "key_points": [
          "关键点 1",
          "关键点 2",
          "关键点 3"
      ],
      "trade_suggestions": {{
          "buy_point": "建议买入范围或点位",
          "sell_point": "建议卖出范围或点位",
          "stop_loss": "建议止损位"
      }},
      "investment_outlook": {{
          "short_term": {{
              "period": "短期 (1-5日)",
              "trend": "偏空/调整 | 看多/反弹 | 震荡/观望",
              "drivers": "核心驱动因素（如：技术指标超买、资金流出）",
              "risk_level": "高风险 (缩量回调中) | 中风险 | 低风险",
              "advice": "具体操作建议（如：等待回踩20日线）"
          }},
          "mid_term": {{
              "period": "中长期 (1-3月)",
              "trend": "看多/蓄势 | 看空/破位 | 中性",
              "drivers": "核心驱动因素（如：政策利好预期、基本面反转）",
              "risk_level": "高价值 (底部抬升) | 高风险 | 中性",
              "advice": "具体操作建议（如：逢低分批建仓）"
          }}
      }}
    }}

    重点关注历史趋势中的技术形态、资金流向数据中的主力动向，以及新闻中的市场情绪。
    """
    
    # 3. Call LLM
    report_content = "LLM based analysis unavailable."
    recommendation = "HOLD"
    
    models_to_try = [
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
    ]
    
    last_error = "No models tried"
    for model_name in models_to_try:
        try:
            print(f"Trying GenAI model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"Success with model: {model_name}")
            report_content = response.text
            # Clean up potential markdown code blocks if the model ignored instructions
            cleaned_content = report_content.replace('```json', '').replace('```', '').strip()
            
            try:
                import json
                parsed_data = json.loads(cleaned_content)
                recommendation = parsed_data.get("recommendation", "HOLD")
                # Store the raw JSON string as content for the frontend to parse
                report_content = cleaned_content
            except json.JSONDecodeError:
                print("Failed to parse JSON response. Falling back to raw text.")
                recommendation = "Review" # Fallback
                
            break # Success
        except Exception as e:
            print(f"Failed with model {model_name}: {e}")
            last_error = e
            continue
    else:
        # If loop finishes without break
        print(f"All models failed. Last error: {last_error}")
        # Return a valid JSON error message
        report_content = '{"summary": "Error generating analysis. Please try again.", "recommendation": "ERROR"}'
        recommendation = "ERROR" # Set recommendation for error case

    return AnalysisReport(
        stock_symbol=symbol,
        stock_name=stock_name,
        report_content=report_content,
        generated_at=datetime.now(),
        price=current_price,
        recommendation=recommendation,
        news_items=news_items
    )
