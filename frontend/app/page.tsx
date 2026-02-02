"use client";

import { useEffect, useState } from "react";
import { fetchStocks, addStock, removeStock, fetchReports, setTimer, triggerAnalysis } from "@/lib/api";
import { Clock, RefreshCw, Activity, Plus, Trash2, FileText, BarChart2, ArrowRight, CheckCircle, ShieldAlert, AlertTriangle, CheckSquare, Zap, LogIn, LogOut, User, X } from "lucide-react";
import { useSession, signIn, signOut } from "next-auth/react";

// ... (existing code)

const OutlookSection = ({ outlook }: { outlook: any }) => {
  if (!outlook) return null;

  return (
    <div className="mt-8 bg-white rounded-xl overflow-hidden text-gray-900 shadow-lg">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-50 text-gray-500 uppercase font-bold tracking-wider text-xs border-b border-gray-100">
            <tr>
              <th className="px-6 py-4">维度</th>
              <th className="px-6 py-4">趋势判断</th>
              <th className="px-6 py-4">核心驱动因素</th>
              <th className="px-6 py-4">风险/机会等级</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {/* Short Term Row */}
            {outlook.short_term && (
              <tr className="hover:bg-gray-50/50 transition-colors">
                <td className="px-6 py-4 font-bold whitespace-nowrap">
                  {outlook.short_term.period || "短期 (1-5日)"}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2 font-bold">
                    {outlook.short_term.trend?.includes("空") || outlook.short_term.trend?.includes("调整") ? (
                      <AlertTriangle className="w-4 h-4 text-orange-500 flex-shrink-0" />
                    ) : (
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                    )}
                    {outlook.short_term.trend}
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-600 max-w-xs">
                  {outlook.short_term.drivers}
                </td>
                <td className="px-6 py-4">
                  <span className="font-medium text-gray-700 block mb-1">
                    {outlook.short_term.risk_level}
                  </span>
                  <p className="text-xs text-gray-500 italic">
                    建议: {outlook.short_term.advice}
                  </p>
                </td>
              </tr>
            )}

            {/* Mid Term Row */}
            {outlook.mid_term && (
              <tr className="hover:bg-gray-50/50 transition-colors">
                <td className="px-6 py-4 font-bold whitespace-nowrap">
                  {outlook.mid_term.period || "中长期 (1-3月)"}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2 font-bold">
                    {outlook.mid_term.trend?.includes("多") || outlook.mid_term.trend?.includes("蓄势") ? (
                      <CheckSquare className="w-4 h-4 text-green-600 flex-shrink-0" />
                    ) : (
                      <Activity className="w-4 h-4 text-blue-500 flex-shrink-0" />
                    )}
                    {outlook.mid_term.trend}
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-600 max-w-xs">
                  {outlook.mid_term.drivers}
                </td>
                <td className="px-6 py-4">
                  <span className="font-medium text-gray-700 block mb-1">
                    {outlook.mid_term.risk_level}
                  </span>
                  <p className="text-xs text-gray-500 italic">
                    建议: {outlook.mid_term.advice}
                  </p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";

interface Stock {
  symbol: string;
  market: string;
  name?: string;
  added_at: string;
}

interface NewsItem {
  title: string;
  content: string;
  sentiment?: string; // '正面', '负面', '中性'
  score?: number;
}

interface Report {
  stock_symbol: string;
  stock_name?: string;
  report_content: string;
  generated_at: string;
  price?: number;
  recommendation?: string;
  news_items?: NewsItem[];
}

const MiniChart = ({ symbol, market }: { symbol: string, market: string }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/stocks/${market}/${symbol}/chart`);
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [symbol, market]);

  if (loading) return <div className="h-10 w-24 bg-gray-700 animate-pulse rounded"></div>;
  if (!data || data.length === 0) return <div className="text-xs text-gray-500">无数据</div>;

  const isUp = data.length > 1 && data[data.length - 1].price >= data[0].price;
  const color = isUp ? "#10b981" : "#ef4444"; // green-500 : red-500

  return (
    <div className="h-12 w-28">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <Line
            type="monotone"
            dataKey="price"
            stroke={color}
            strokeWidth={2}
            dot={false}
          />
          <YAxis domain={['auto', 'auto']} hide={true} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default function Home() {
  const { data: session, status } = useSession();
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isGuestPromptOpen, setIsGuestPromptOpen] = useState(false);


  const [stocks, setStocks] = useState<Stock[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [newSymbol, setNewSymbol] = useState("");
  const [market, setMarket] = useState("HK");
  const [timerTime, setTimerTime] = useState("09:00");
  const [loading, setLoading] = useState(false);
  const [dateFilter, setDateFilter] = useState<"today" | "yesterday">("today");

  // Get user identifier (email or name for GitHub users without email)
  const userIdentifier = session?.user?.email || session?.user?.name || null;

  useEffect(() => {
    if (status === "loading") return;
    loadData();
    // Poll for reports every 10 seconds just in case
    const interval = setInterval(loadReports, 10000);
    return () => clearInterval(interval);
  }, [dateFilter, session, status]); // Added status dependency

  // Load data logic handling both local and remote
  const loadData = async () => {
    // Prevent loading data while session state is unknown
    if (status === "loading") return;

    try {
      if (status === "authenticated" && userIdentifier) {
        // Logged in: Fetch from server
        console.log("Loading stocks for user:", userIdentifier);
        try {
          const s = await fetchStocks(userIdentifier);
          console.log("Fetched stocks:", s);
          setStocks(s);
        } catch (err) {
          console.error("Fetch stocks failed", err);
        }
      } else if (status === "unauthenticated") {
        // Guest: Clear stocks
        console.log("Guest mode - clearing stocks");
        setStocks([]);
      }
      // If authenticated but no identifier, keep current stocks (don't clear)

      // Reports are always global for now (or could be filtered)
      loadReports();
    } catch (e) {
      console.error(e);
    }
  };

  const loadReports = async () => {
    try {
      const r = await fetchReports(dateFilter);
      setReports(r);
    } catch (e) { console.error(e); }
  }

  const handleAddStock = async (e: React.FormEvent) => {
    e.preventDefault();
    const symbol = newSymbol.trim().toUpperCase();
    if (!symbol) return;

    // Optimistic Update Object
    const tempStock: Stock = {
      symbol: symbol,
      market: market,
      name: "正在获取名称...",
      added_at: new Date().toISOString()
    };

    if (userIdentifier) {
      console.log("Adding stock for user:", userIdentifier);
      // Logged in: Add to server
      // 1. Optimistic Add
      setStocks(prev => [tempStock, ...prev]);
      setNewSymbol("");
      try {
        // 2. API Call - Get the confirmed stock object
        const confirmedStock = await addStock(symbol, market, userIdentifier);
        console.log("Stock added successfully:", confirmedStock);

        // 3. Update state with real data (avoids race condition with fetchStocks)
        setStocks(prev => prev.map(s =>
          (s.symbol === symbol && s.market === market) ? confirmedStock : s
        ));
      } catch (e: any) {
        // Rollback on error
        console.error("Add stock failed:", e);
        setStocks(prev => prev.filter(s => s.symbol !== symbol || s.market !== market));
        alert(e.message || "添加股票出错");
      }
    } else if (status === "authenticated") {
      // Authenticated but no identifier - this shouldn't happen
      alert("无法获取用户信息，请重新登录");
      console.error("User authenticated but no identifier available. Session:", session);
    } else {
      // Guest: Show login prompt
      setIsGuestPromptOpen(true);
    }
  };

  const handleRemove = async (symbol: string) => {
    if (userIdentifier) {
      try {
        await removeStock(symbol, userIdentifier);
        loadData();
      } catch (e: any) {
        alert(e.message || "删除失败");
      }
    } else {
      alert("游客模式下无法删除股票");
    }
  };

  const handleSetTimer = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await setTimer(timerTime);
      alert(`Timer set to ${timerTime}`);
    } catch (e) {
      alert("Error setting timer");
    }
  };

  const handleRunNow = async () => {
    setLoading(true);
    try {
      await triggerAnalysis();
      alert("分析任务已在后台启动，请稍后刷新查看报告。");
    } catch (e) {
      alert("启动失败");
    } finally {
      setLoading(false);
    }
  };




  return (
    <main className="min-h-screen bg-gray-900 text-gray-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">

        {/* Header */}
        <header className="flex justify-between items-center border-b border-gray-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              智能股票分析助手
            </h1>
            <p className="text-gray-400 mt-2">AI 驱动的市场洞察与自动报告系统</p>
          </div>
          <div className="flex items-center gap-4">
            {session ? (
              <div className="flex items-center gap-3 bg-gray-800/50 px-3 py-1.5 rounded-full border border-gray-700">
                {session.user?.image ? (
                  <img src={session.user.image} alt="User" className="w-6 h-6 rounded-full" />
                ) : (
                  <User className="w-4 h-4 text-gray-400" />
                )}
                <span className="text-sm text-gray-300">{session.user?.name || session.user?.email}</span>
                <button onClick={() => signOut()} className="p-1 hover:text-red-400 transition" title="Sign Out">
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsLoginModalOpen(true)}
                className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg text-sm border border-gray-700 transition"
              >
                <LogIn className="w-4 h-4" />
                <span className="hidden sm:inline">登录 / 注册</span>
              </button>
            )}

            <div className="h-8 w-px bg-gray-700 mx-2 hidden sm:block"></div>
            <div className="flex items-center gap-2 bg-gray-800 px-4 py-2 rounded-lg border border-gray-700">
              <Clock className="w-4 h-4 text-blue-400" />
              <input
                type="time"
                value={timerTime}
                onChange={(e) => setTimerTime(e.target.value)}
                className="bg-transparent border-none focus:ring-0 text-sm"
              />
              <button
                onClick={handleSetTimer}
                className="text-xs bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded transition"
              >
                设定
              </button>
            </div>
            <button
              onClick={handleRunNow}
              disabled={loading}
              className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600 px-5 py-2.5 rounded-lg font-medium hover:opacity-90 transition disabled:opacity-50 shadow-lg shadow-green-900/20"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              {loading ? "分析中..." : "立即运行分析"}
            </button>
          </div>
        </header>

        {/* Watchlist Section */}
        <section className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 text-purple-400" />
              自选关注列表
            </h2>
            <span className="text-sm text-gray-500">{stocks.length} 个关注中</span>
          </div>

          <div className="space-y-3">
            {/* Add New Row */}
            <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 flex flex-col md:flex-row gap-4 items-center hover:border-blue-500/50 transition">
              <div className="flex gap-2 flex-1 w-full">
                <select
                  value={market}
                  onChange={(e) => setMarket(e.target.value)}
                  className="bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:border-blue-500 outline-none cursor-pointer"
                >
                  <option value="HK">港股 (HK)</option>
                  <option value="US">美股 (US)</option>
                </select>
                <input
                  type="text"
                  placeholder="输入股票代码 (如 0700 或 AAPL)"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value)}
                  className="bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 flex-1 text-sm focus:border-blue-500 outline-none"
                />
              </div>
              <button
                onClick={handleAddStock}
                className="w-full md:w-auto bg-blue-600 hover:bg-blue-700 active:scale-95 px-6 py-2 rounded-lg text-sm font-medium transition-all flex justify-center items-center gap-2 cursor-pointer shadow-lg shadow-blue-900/20"
              >
                <Plus className="w-4 h-4" /> 添加股票
              </button>
            </div>

            {/* Stock List */}
            <div className="bg-gray-800 border border-gray-700 rounded-xl divide-y divide-gray-700">
              {stocks.map((stock) => (
                <div key={`${stock.market}-${stock.symbol}`} className="p-4 flex items-center justify-between hover:bg-gray-750 transition-colors group">
                  <div className="flex items-center gap-6 flex-1">
                    <div className="w-24">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold bg-gray-700 px-1 py-0.5 rounded text-gray-400">{stock.market}</span>
                        <span className="text-base font-bold text-gray-100">{stock.symbol}</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">代码</div>
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="text-base font-semibold text-blue-400 truncate">
                        {stock.name || "正在获取名称..."}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">公司名称</div>
                    </div>

                    <div className="hidden md:block">
                      <MiniChart symbol={stock.symbol} market={stock.market} />
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handleRemove(stock.symbol)}
                      className="text-gray-500 hover:text-red-400 hover:bg-red-400/10 p-2 rounded-lg transition-colors cursor-pointer active:scale-90"
                      title="删除"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))}
              {stocks.length === 0 && (
                <div className="p-8 text-center text-gray-500">
                  关注列表为空，请在上方添加股票
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Analysis Reports Section */}
        <section className="space-y-6 pt-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5 text-yellow-500" />
              智能分析报告
            </h2>
            <div className="flex items-center gap-3">
              {/* Date Filter Buttons */}
              <div className="flex items-center gap-2 bg-gray-800 rounded-lg p-1 border border-gray-700">
                <button
                  onClick={() => setDateFilter("today")}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${dateFilter === "today"
                    ? "bg-blue-600 text-white shadow-lg"
                    : "text-gray-400 hover:text-gray-200"
                    }`}
                >
                  今天
                </button>
                <button
                  onClick={() => setDateFilter("yesterday")}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${dateFilter === "yesterday"
                    ? "bg-blue-600 text-white shadow-lg"
                    : "text-gray-400 hover:text-gray-200"
                    }`}
                >
                  昨天
                </button>
              </div>
              <button
                onClick={loadReports}
                className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1 cursor-pointer transition-colors"
              >
                <RefreshCw className="w-3 h-3" /> 刷新
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-8">
            {reports.map((report, idx) => {
              let parsed: any = {};
              let isJson = false;
              try {
                parsed = JSON.parse(report.report_content);
                isJson = true;
              } catch (e) { }

              return (
                <div key={idx} className="bg-gray-800 border border-gray-700 rounded-2xl overflow-hidden shadow-2xl transition-all duration-300 hover:shadow-blue-900/10">
                  {/* Report Header */}
                  <div className="bg-gray-800/50 p-6 border-b border-gray-700 md:flex items-center justify-between gap-6">
                    <div className="flex items-center gap-4 mb-4 md:mb-0">
                      <div className={`p-4 rounded-2xl shadow-inner ${report.recommendation === 'BUY' ? 'bg-green-500/10' :
                        report.recommendation === 'SELL' ? 'bg-red-500/10' : 'bg-yellow-500/10'
                        }`}>
                        <BarChart2 className={`w-8 h-8 ${report.recommendation === 'BUY' ? 'text-green-400' :
                          report.recommendation === 'SELL' ? 'text-red-400' : 'text-yellow-400'
                          }`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-3">
                          <h3 className="text-3xl font-extrabold tracking-tight">{report.stock_symbol}</h3>
                          {report.stock_name && report.stock_name !== report.stock_symbol && (
                            <span className="text-xl text-blue-400 font-bold hidden sm:inline-block">
                              {report.stock_name}
                            </span>
                          )}
                          <div className={`px-4 py-1 rounded-full text-xs font-bold uppercase tracking-widest border ${report.recommendation === 'BUY' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
                            report.recommendation === 'SELL' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                              'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
                            }`}>
                            {report.recommendation === 'BUY' ? '建议买入' :
                              report.recommendation === 'SELL' ? '建议卖出' : '建议持有'}
                          </div>
                        </div>
                        <p className="text-sm text-gray-500 mt-1 font-medium">
                          报告生成: {new Date(report.generated_at).toLocaleString('zh-CN')}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-8 text-right bg-gray-900/40 p-4 rounded-xl border border-gray-700/50">
                      <div>
                        <p className="text-[10px] text-gray-500 uppercase font-black tracking-widest mb-1">当前行情</p>
                        <p className="text-2xl font-mono font-bold text-white leading-none">
                          {report.price ? `$${report.price.toFixed(2)}` : "N/A"}
                        </p>
                      </div>
                      <div className="h-10 w-[1px] bg-gray-700"></div>
                      <div>
                        <p className="text-[10px] text-gray-500 uppercase font-black tracking-widest mb-1">风险评估</p>
                        <div className={`text-lg font-bold leading-none ${parsed.risk_level === 'High' ? 'text-red-400' :
                          parsed.risk_level === 'Medium' ? 'text-yellow-400' : 'text-green-400'
                          }`}>
                          {parsed.risk_level === 'High' ? '高风险' :
                            parsed.risk_level === 'Medium' ? '中等风险' : '低风险'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Report Content */}
                  <div className="p-8 space-y-8">
                    {isJson ? (
                      <>
                        {/* Summary Block */}
                        <div className="relative">
                          <div className="absolute -left-4 top-0 bottom-0 w-1 bg-blue-500 rounded-full"></div>
                          <p className="text-xl font-medium text-gray-100 italic leading-relaxed pl-2">
                            "{parsed.summary}"
                          </p>
                        </div>

                        <div className="grid md:grid-cols-2 gap-8">
                          {/* Left Column: Analysis Sections */}
                          <div className="space-y-6">
                            <div className="bg-gray-900/30 p-5 rounded-2xl border border-gray-700/50">
                              <h4 className="text-blue-400 text-sm font-bold flex items-center gap-2 mb-3">
                                <Activity className="w-4 h-4" /> 资金流向分析
                              </h4>
                              <p className="text-gray-300 text-sm leading-relaxed">
                                {parsed.money_flow}
                              </p>
                            </div>
                            <div className="bg-gray-900/30 p-5 rounded-2xl border border-gray-700/50">
                              <h4 className="text-purple-400 text-sm font-bold flex items-center gap-2 mb-3">
                                <BarChart2 className="w-4 h-4" /> 技术指标分析
                              </h4>
                              <p className="text-gray-300 text-sm leading-relaxed">
                                {parsed.technical_analysis}
                              </p>
                            </div>
                          </div>

                          {/* Right Column: Recommendations & Points */}
                          <div className="space-y-6">
                            <div className="bg-emerald-500/5 p-6 rounded-2xl border border-emerald-500/20">
                              <h4 className="text-emerald-400 text-sm font-bold flex items-center gap-2 mb-4">
                                <ArrowRight className="w-4 h-4" /> 买卖点位建议
                              </h4>
                              <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gray-900/60 p-3 rounded-xl border border-gray-700">
                                  <span className="text-[10px] text-gray-500 block mb-1">建议买入</span>
                                  <span className="text-green-400 font-bold">{parsed.trade_suggestions?.buy_point || "观察中"}</span>
                                </div>
                                <div className="bg-gray-900/60 p-3 rounded-xl border border-gray-700">
                                  <span className="text-[10px] text-gray-500 block mb-1">建议卖出</span>
                                  <span className="text-red-400 font-bold">{parsed.trade_suggestions?.sell_point || "观察中"}</span>
                                </div>
                                <div className="col-span-2 bg-gray-900/60 p-3 rounded-xl border border-gray-700 flex justify-between items-center">
                                  <span className="text-[10px] text-gray-500 uppercase tracking-widest">止损参考</span>
                                  <span className="text-orange-400 font-bold">{parsed.trade_suggestions?.stop_loss || "未设置"}</span>
                                </div>
                              </div>
                            </div>

                            <div className="bg-gray-900/30 p-5 rounded-2xl border border-gray-700/50">
                              <h4 className="text-gray-400 text-sm font-bold flex items-center gap-2 mb-3">
                                <CheckCircle className="w-4 h-4" /> 核心利好/风险点
                              </h4>
                              <ul className="space-y-2">
                                {parsed.key_points?.map((point: string, i: number) => (
                                  <li key={i} className="flex gap-2 text-xs text-gray-400">
                                    <span className="text-blue-500 font-bold">•</span>
                                    {point}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>

                        {/* News Section */}
                        {(
                          <div className="mt-8 bg-gradient-to-br from-blue-500/5 to-purple-500/5 p-6 rounded-2xl border border-blue-500/20">
                            <h4 className="text-blue-400 text-sm font-bold flex items-center gap-2 mb-4">
                              <FileText className="w-4 h-4" /> 最新动态信息
                            </h4>
                            {report.news_items && report.news_items.length > 0 ? (
                              <div className="space-y-3">
                                {report.news_items.slice(0, 3).map((news, newsIdx) => {
                                  const sentiment = news.sentiment || '中性';
                                  const sentimentColor = sentiment === '正面' ? 'text-green-400 bg-green-500/10 border-green-500/30' :
                                    sentiment === '负面' ? 'text-red-400 bg-red-500/10 border-red-500/30' :
                                      'text-gray-400 bg-gray-500/10 border-gray-500/30';

                                  return (
                                    <div key={newsIdx} className="flex gap-3 items-start">
                                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
                                        <span className="text-blue-400 text-xs font-bold">{newsIdx + 1}</span>
                                      </div>
                                      <div className="flex-1 space-y-2">
                                        <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                                          {news.content}
                                        </p>
                                        {news.score && (
                                          <div className="mt-2 w-full bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
                                            <div
                                              className={`h-full rounded-full ${news.score >= 70 ? 'bg-green-500' : news.score >= 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                              style={{ width: `${news.score}%` }}
                                            ></div>
                                          </div>
                                        )}
                                        <span className={`inline-block px-2 py-0.5 rounded-md text-[10px] font-bold border ${sentimentColor} mt-2`}>
                                          {sentiment}
                                        </span>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            ) : (
                              <div className="text-gray-500 text-sm italic py-4 text-center">
                                暂无最新敏感动态信息 (可能是因为数据源限制或今日无重大新闻)
                              </div>
                            )}
                          </div>
                        )}
                        {/* Investment Outlook Table */}
                        <OutlookSection outlook={parsed.investment_outlook} />
                      </>
                    ) : (
                      <div className="prose prose-invert max-w-none">
                        <p className="whitespace-pre-wrap text-gray-300 leading-relaxed">{report.report_content}</p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {reports.length === 0 && (
              <div className="text-center py-24 bg-gray-800/30 rounded-3xl border-2 border-dashed border-gray-700">
                <FileText className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                <p className="text-gray-500 text-xl font-medium">暂无深度分析报告</p>
                <p className="text-gray-600 text-sm mt-2 max-w-xs mx-auto">
                  添加您感兴趣的股票并点击上方按钮，AI 助手将为您生成专业的市场深度分析。
                </p>
              </div>
            )}
          </div>
        </section>
      </div>
      {/* Login Modal */}
      {isLoginModalOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setIsLoginModalOpen(false)}
        >
          <div
            className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md p-6 shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setIsLoginModalOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-xl font-bold mb-2">欢迎回来</h2>
            <p className="text-gray-400 text-sm mb-6">登录以同步您的自选股列表和个性化设置</p>

            <div className="space-y-3">
              <button
                onClick={() => signIn('github')}
                className="w-full flex items-center justify-center gap-3 bg-[#24292e] hover:bg-[#2f363d] text-white p-3 rounded-lg font-medium transition border border-gray-700"
              >
                {/* Generic Code Icon as Github placeholder if needed, or just text */}
                <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" /></svg>
                Github 登录
              </button>

              <button
                onClick={() => signIn('google')}
                className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-100 text-gray-900 p-3 rounded-lg font-medium transition"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24"><path fill="#EA4335" d="M5.266 9.765A7.077 7.077 0 0 1 12 4.909c1.69 0 3.218.6 4.418 1.582L19.91 3C17.782 1.145 15.087 0 12 0 7.31 0 3.263 2.691 1.288 6.601l3.978 3.164z" /><path fill="#34A853" d="M16.04 18.013c-1.09.703-2.474 1.078-4.04 1.078a7.077 7.077 0 0 1-6.723-4.823l-3.998 3.066C3.253 21.352 7.291 24 12 24c2.93 0 5.414-1.041 7.23-2.806l-3.19-3.181z" /><path fill="#4A90E2" d="M19.834 21.194c2.148-1.996 3.428-4.912 3.428-8.204 0-.756-.062-1.487-.178-2.193H12v4.205h6.392c-.276 1.48-.968 2.593-2.358 3.193l3.8 3.003z" /><path fill="#FBBC05" d="M5.277 14.168A7.097 7.097 0 0 1 4.909 12c0-.743.125-1.46.368-2.235l-3.978-3.164C.453 8.353 0 10.133 0 12c0 1.942.49 3.663 1.299 5.215l3.978-3.047z" /></svg>
                Google 登录
              </button>


            </div>

            <p className="text-center text-xs text-gray-600 mt-6">
              登录即代表您同意我们的服务条款和隐私政策
            </p>
          </div>
        </div>
      )}

      {/* Guest Prompt Modal */}
      {isGuestPromptOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setIsGuestPromptOpen(false)}
        >
          <div
            className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md p-6 shadow-2xl relative"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setIsGuestPromptOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="text-center">
              <div className="w-16 h-16 bg-yellow-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <ShieldAlert className="w-8 h-8 text-yellow-400" />
              </div>
              <h2 className="text-xl font-bold mb-2">需要登录</h2>
              <p className="text-gray-400 text-sm mb-6">
                游客模式无法添加股票。请通过 GitHub 或 Google 登录后添加自选股，您的数据将安全保存在云端。
              </p>

              <div className="space-y-3">
                <button
                  onClick={() => {
                    setIsGuestPromptOpen(false);
                    signIn('github');
                  }}
                  className="w-full flex items-center justify-center gap-3 bg-[#24292e] hover:bg-[#2f363d] text-white p-3 rounded-lg font-medium transition border border-gray-700"
                >
                  <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" /></svg>
                  Github 登录
                </button>

                <button
                  onClick={() => {
                    setIsGuestPromptOpen(false);
                    signIn('google');
                  }}
                  className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-100 text-gray-900 p-3 rounded-lg font-medium transition"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24"><path fill="#EA4335" d="M5.266 9.765A7.077 7.077 0 0 1 12 4.909c1.69 0 3.218.6 4.418 1.582L19.91 3C17.782 1.145 15.087 0 12 0 7.31 0 3.263 2.691 1.288 6.601l3.978 3.164z" /><path fill="#34A853" d="M16.04 18.013c-1.09.703-2.474 1.078-4.04 1.078a7.077 7.077 0 0 1-6.723-4.823l-3.998 3.066C3.253 21.352 7.291 24 12 24c2.93 0 5.414-1.041 7.23-2.806l-3.19-3.181z" /><path fill="#4A90E2" d="M19.834 21.194c2.148-1.996 3.428-4.912 3.428-8.204 0-.756-.062-1.487-.178-2.193H12v4.205h6.392c-.276 1.48-.968 2.593-2.358 3.193l3.8 3.003z" /><path fill="#FBBC05" d="M5.277 14.168A7.097 7.097 0 0 1 4.909 12c0-.743.125-1.46.368-2.235l-3.978-3.164C.453 8.353 0 10.133 0 12c0 1.942.49 3.663 1.299 5.215l3.978-3.047z" /></svg>
                  Google 登录
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
