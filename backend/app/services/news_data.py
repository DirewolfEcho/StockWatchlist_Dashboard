from tavily import TavilyClient
import os
from typing import List

def get_stock_news(symbol: str, market: str, price_context: dict = None) -> List[dict]:
    """
    Search for latest news and generate a consolidated senior analyst report.
    Returns a single 'news item' containing the comprehensive analysis.
    
    price_context: Optional dict containing {'price': float, 'high': float, 'low': float} for fact checking.
    """
    api_keys = [
        "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",
        "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"
    ]
    
    # Get stock name for context
    try:
        from .stock_data import get_stock_name
        stock_name = get_stock_name(symbol, market)
    except:
        stock_name = None
    
    results = []
    
    # Try keys in order until one works
    for api_key in api_keys:
        try:
            # 1. Search for news
            tavily = TavilyClient(api_key=api_key)
            
            query = f"{symbol} stock business news analysis"
            if market == 'HK':
                query += " Hong Kong market"
            elif market == 'US':
                query += " US market"
                
            # Fetch more context for the analyst
            response = tavily.search(query=query, search_depth="advanced", max_results=10)
            results = response.get('results', [])
            
            if results:
                print(f"Successfully fetched news using key ending in ...{api_key[-4:]}")
                break
                
        except Exception as e:
            print(f"Tavily API key {api_key[:10]}... failed: {e}")
            continue
            
    if not results:
        print("All Tavily API keys failed or returned no results.")
        return []
            
    # 2. Prepare context for LLM
    news_context = ""
    for i, res in enumerate(results):
        news_context += f"News {i+1}: {res.get('title', '')}\n{res.get('content', '')}\nDate: {res.get('published_date', 'Unknown')}\n\n"
        
    # 3. Call LLM for comprehensive analysis
    try:
        analysis_result = _generate_analyst_summary(news_context, symbol, stock_name, price_context)
        
        if analysis_result.get('is_valid', False):
            # Format the content as requested
            overview_items = analysis_result.get('overview_items', [])
            sentiment_summary = analysis_result.get('sentiment_summary', '')
            sentiment_score = analysis_result.get('sentiment_score', 50)
            
            # Combine into the display format
            # Use bullet points for overview items
            formatted_overview = "【最新动态概述】\n"
            for item in overview_items:
                formatted_overview += f"• {item.get('content', '')} ({item.get('sentiment', '中性')})\n"
            
            full_content = f"{formatted_overview}\n【最新动态总结】\n{sentiment_summary} (综合情绪分: {sentiment_score}/100)"
            
            return [{
                'title': '资深研究员市场动态综述',
                'content': full_content,
                'sentiment': analysis_result.get('overall_sentiment', '中性'),
                'score': sentiment_score
            }]
        else:
            return []
    except Exception as e:
        print(f"Error processing news analysis: {e}")
        return []

def _translate_and_validate_news(title: str, content: str, symbol: str, stock_name: str = None) -> dict:
    """
    Use LLM to extract core insights and validate content quality.
    Acts as a senior equity analyst focusing on non-price events.
    Returns dict with 'is_valid' and 'summary' fields.
    Ensures the summary explicitly mentions the stock.
    """
    try:
        import google.generativeai as genai
        
        import os
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
        if not GEMINI_API_KEY:
            return {"is_valid": True, "summary": ""}
        genai.configure(api_key=GEMINI_API_KEY)
        
        stock_identifier = f"{stock_name}({symbol})" if stock_name else symbol
        
        from datetime import datetime, timedelta
        
        # Calculate the date 1 week ago
        one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y年%m月%d日")
        current_date = datetime.now().strftime("%Y年%m月%d日")
        
        prompt = f"""你是一位拥有 15 年经验的资深二级市场研究员，你的专长是**"去伪存真"**。

新闻标题: {title}
新闻内容: {content}
目标股票: {stock_identifier}
当前日期: {current_date}

核心约束（违者判定为无效）：

1. 严禁陈旧信息：
   - 禁止提及 IPO、历史发行价、去年的财报等陈旧数据
   - 所有信息必须是 {one_week_ago} 之后（最近1周内）发生的
   - 如果新闻内容是陈旧的，直接判定为无效

2. 严禁纯量价描述：
   - 禁止出现"股价下滑"、"成交活跃"、"资金流向"、"涨跌幅百分比"等低价值实时行情
   - 如果提到股价变动，必须说明是哪段时间（且必须在最近1周内），以及背后的原因事件

3. 真实性核查：
   - 提到的任何研报观点必须说明是哪家机构（如中金、美银、高盛等）
   - 禁止使用"有消息称"、"相关ETF受到关注"、"市场传闻"等模棱两可的废话
   - 如果无法确认信息来源，判定为无效

调研重点（至少包含一项）：

1. 核心业务变动：
   - 产能利用率变化、新订单签单
   - 新产品流片/上市、关键技术突破
   - 资产重组、并购、分拆等资本运作

2. 机构逻辑：
   - 知名券商最新的研报核心逻辑（为什么看好/看淡）
   - 必须说明机构名称和具体理由，而非仅仅是目标价

3. 行业共振：
   - 影响该个股的重大行业政策
   - 竞对动态对该股的影响

4. 负面新闻：
   - 重大制裁、监管机构问询
   - 高管变动、诉讼等

【输出格式】
请以JSON格式返回，不要包含markdown格式：
{{
  "is_valid": true/false,
  "summary": "详细的事件描述，包含具体细节（如涨价幅度、机构名称、时间段等），不要在描述中添加（正面）（负面）（中性）标签",
  "sentiment": "正面/负面/中性",
  "reason": "判断为有效或无效的原因"
}}

【总结要求】
1. 必须是中文，明确提及该股票
2. 必须包含具体细节：
   - 提到涨价要说明涨多少
   - 提到研报要说明机构名称和核心逻辑
   - 提到股价变动要说明是哪段时间（必须在最近1周内）
3. 完整句子，不能以"..."结尾
4. 不能包含"加载中"、"待披露"、"有消息称"等不确定信息
5. **不要在summary中添加（正面）（负面）（中性）标签**，情绪判断单独放在sentiment字段

【判断标准】
- 有效：最近1周内 + 包含调研重点中至少一项 + 有具体细节 + 信息来源明确 + 无量价废话
- 无效：陈旧信息 OR 纯量价描述 OR 信息来源模糊 OR 缺乏细节 OR 包含不确定表述

【示例】
有效: "苹果公司(AAPL)于1月25日宣布以35亿美元收购AI初创公司Q.ai，该交易预计在Q2完成。高盛在1月27日的研报中指出，此次收购将帮助苹果在生成式AI领域缩小与微软的差距，并上调评级至买入"
无效: "苹果股价上涨0.46%，成交量达到7960万股"
无效: "有消息称苹果正在开发新产品"
无效: "苹果去年发布了Vision Pro头显"
"""
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        import json
        result_text = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(result_text)
        
        # Validate the result
        is_valid = result.get('is_valid', False)
        summary = result.get('summary', '').strip()
        sentiment = result.get('sentiment', '中性')
        
        # Additional validation checks
        if is_valid and summary:
            # Check for incomplete sentences (ends with ...)
            if summary.endswith('...') or summary.endswith('…'):
                is_valid = False
                result['reason'] = '句子不完整，以省略号结尾'
            
            # Check for loading/pending indicators
            invalid_keywords = ['加载中', '待披露', '暂无数据', '数据加载', '正在加载', '敬请期待', '暂无', '待定']
            for keyword in invalid_keywords:
                if keyword in summary:
                    is_valid = False
                    result['reason'] = f'包含不确定信息: {keyword}'
                    break
            
            # Check for forbidden price/volume content
            price_keywords = [
                '股价', '收盘价', '开盘价', '最高价', '最低价',
                '成交量', '换手率', '交易量',
                '资金流入', '资金流出', '南向资金', '北向资金',
                'KDJ', 'MACD', 'RSI',
                '市值', '市盈率', 'PE', 'PB',
                '52周', '涨', '跌', '上涨', '下跌'
            ]
            
            # Allow some price keywords if they're part of a larger business context
            # But if the summary is dominated by price talk, reject it
            price_mention_count = sum(1 for kw in price_keywords if kw in summary)
            if price_mention_count >= 3:  # Too many price-related terms
                is_valid = False
                result['reason'] = '包含过多价格/成交量相关信息，应聚焦事件本身'
            
            # Check minimum length (too short likely means no real content)
            if len(summary) < 20:
                is_valid = False
                result['reason'] = '内容过短，信息不足'
            
            # Check if stock is mentioned
            stock_mentioned = False
            # Check for stock code
            if symbol in summary:
                stock_mentioned = True
            # Check for stock name (if provided)
            elif stock_name and stock_name in summary:
                stock_mentioned = True
            # Check for partial code match (e.g., "00700" vs "700")
            elif symbol.lstrip('0') in summary:
                stock_mentioned = True
            
            if not stock_mentioned:
                is_valid = False
                result['reason'] = f'总结中未提及该股票 {stock_identifier}'
            
            # Check if summary contains English (should be all Chinese)
            # Allow up to 50% English for proper nouns (company names, etc.)
            import re
            english_ratio = len(re.findall(r'[a-zA-Z]', summary)) / max(len(summary), 1)
            if english_ratio > 0.5:  # More than 50% English characters
                is_valid = False
                result['reason'] = '总结包含过多英文，应全部翻译成中文'
            
            # Validate sentiment tag
            if sentiment not in ['正面', '负面', '中性']:
                sentiment = '中性'
        
        return {
            'is_valid': is_valid,
            'summary': summary if is_valid else '',
            'sentiment': sentiment if is_valid else '中性',
            'reason': result.get('reason', '')
        }
        
    except Exception as e:
        print(f"Error validating news: {e}")
        return {
            'is_valid': False,
            'summary': '',
            'sentiment': '中性',
            'reason': f'Error: {str(e)}'
        }

def _generate_analyst_summary(news_context: str, symbol: str, stock_name: str = None, price_context: dict = None) -> dict:
    """
    Use LLM to generate a senior analyst summary from raw news context.
    """
    try:
        import google.generativeai as genai
        
        import os
        GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
        if not GEMINI_API_KEY:
            return {"summary": "API key not configured"}
        genai.configure(api_key=GEMINI_API_KEY)
        
        stock_identifier = f"{stock_name}({symbol})" if stock_name else symbol
        
        from datetime import datetime, timedelta
        one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y年%m月%d日")
        current_date = datetime.now().strftime("%Y年%m月%d日")
        
        # Format price verification data
        verification_instruction = ""
        if price_context:
            price = price_context.get('price', 'N/A')
            verification_instruction = f"""
特别注意数据核实：
我通过实时接口获取的今日（{current_date}）行情数据如下：
- 最新价: {price}
- 价格范围: {price_context.get('low', 'N/A')} - {price_context.get('high', 'N/A')} (仅供参考)

严禁在报告中引用与上述数据严重偏离的新闻价格！
如果新闻中提到“今日股价暴涨至XX”，但与我的实时数据不符，说明新闻可能是旧闻或错误的，请务必剔除或修正该信息。
例如：如果新闻说今天涨了10%到20元，但实际价格只有15元，这绝对是错误/过时新闻，直接忽略该条新闻。
"""

        prompt = f"""你是一位拥有 15 年经验的资深二级市场研究员，你的专长是**"去伪存真"**。
请基于以下原始新闻资讯，为 {stock_identifier} 撰写一份【最新动态信息】分析。

当前日期: {current_date}
参考新闻资讯:
{news_context}

{verification_instruction}

核心约束（违者判定为无效）：

0. **语言强制**：所有输出内容（包括概述、总结）必须严格使用**简体中文**。如果原始新闻是英文，必须翻译成流畅的中文。

1. 严禁陈旧信息：
   - 剔除所有 {one_week_ago} 之前发生的旧闻（如去年的财报、IPO等）
   - 如果所有新闻都是陈旧的，请返回无效

2. 严禁纯量价描述：
   - 禁止出现"股价下滑"、"成交活跃"、"资金流向"、"涨跌幅百分比"等低价值实时行情描述，除非是为了验证新闻真实性。
   - 关注业务本质

3. 真实性核查：
   - 提到的研报观点必须说明机构名称（中金、美银等）
   - 禁止使用"有消息称"、"传闻"等模糊表述

调研重点（必须包含实质性内容）：
- 核心业务变动（产能、订单、新产品、并购）
- 机构逻辑（明确机构名称和看好/看淡的深层逻辑）
- 行业共振（政策、竞对）
- 负面新闻（制裁、监管）

【输出格式要求】
请以严格的JSON格式返回：
{{
  "is_valid": true,
  "overview_items": [
    {{
        "content": "具体的事件描述1（包含细节）",
        "sentiment": "正面/负面/中性"
    }},
    {{
        "content": "具体的事件描述2（包含细节）",
        "sentiment": "正面/负面/中性"
    }}
  ],
  "sentiment_summary": "概括所有动态的总结（2-3句话），提供深度洞察",
  "sentiment_score": 0-100 (0为极度悲观，50中性，100极度乐观),
  "overall_sentiment": "正面/负面/中性"
}}

如果提供的资讯中没有任何最近1周的有价值信息，请返回:
{{ "is_valid": false }}
"""
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        import json
        result_text = response.text.replace('```json', '').replace('```', '').strip()
        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            print("Error parsing JSON from analyst summary")
            return {"is_valid": False}
            
    except Exception as e:
        print(f"Error generating analyst summary: {e}")
        return {"is_valid": False}

def get_stock_news_summary(symbol: str, market: str) -> str:
    """
    Get news as a formatted string for LLM analysis.
    """
    news_items = get_stock_news(symbol, market)
    if not news_items:
        return "No recent news available."
    
    news_summary = ""
    for idx, item in enumerate(news_items, 1):
        news_summary += f"{idx}. {item['content']}\n"
    
    return news_summary
