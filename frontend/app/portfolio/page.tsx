"use client";
import { useEffect, useState, useMemo } from "react";
import TopAppBar from "../components/TopAppBar";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceDot, ReferenceLine } from "recharts";

export default function PortfolioPage() {
  const [data, setData] = useState<any>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [individualCharts, setIndividualCharts] = useState<Record<string, any[]>>({});
  const [history, setHistory] = useState<any[]>([]);
  const [timeRange, setTimeRange] = useState<string>("1mo");

  useEffect(() => {
    fetch("http://localhost:8000/api/portfolio")
      .then(res => res.json())
      .then(resData => setData(resData))
      .catch(console.error);

    fetch("http://localhost:8000/api/portfolio/history")
      .then(res => res.json())
      .then(resData => setHistory(resData.history || []))
      .catch(console.error);
  }, []);

  useEffect(() => {
    fetch(`http://localhost:8000/api/portfolio/chart?range=${timeRange}`)
      .then(res => res.json())
      .then(resData => setChartData(resData.chart || []))
      .catch(console.error);

    // Refresh individual charts if they exist
    if (data?.portfolio) {
      data.portfolio.forEach((pos: any) => {
        fetch(`http://localhost:8000/api/portfolio/stock-chart/${pos.ticker}?range=${timeRange}`)
          .then(res => res.json())
          .then(resData => {
            setIndividualCharts(prev => ({...prev, [pos.ticker]: resData.chart || []}));
          })
          .catch(console.error);
      });
    }
  }, [timeRange, data?.portfolio]);

  const handleSell = async (ticker: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/portfolio/remove`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker })
      });
      if (res.ok) {
        window.location.reload();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const getMarkers = (chart: any[], isIndividual: boolean, ticker?: string) => {
    if (!chart || chart.length === 0) return [];
    const relevant = isIndividual ? history.filter(h => h.ticker === ticker) : history;
    const markersMap = new Map();
    
    relevant.forEach(h => {
        const ts = new Date(h.timestamp).getTime() / 1000;
        let closest = chart[0];
        let minDiff = Math.abs(ts - chart[0].raw_ts);
        for(let point of chart) {
            const diff = Math.abs(ts - point.raw_ts);
            if (diff < minDiff) {
                minDiff = diff;
                closest = point;
            }
        }
        
        const key = closest.date;
        if (!markersMap.has(key)) {
            markersMap.set(key, { date: key, value: closest.value, type: h.action, count: 1 });
        } else {
            const existing = markersMap.get(key);
            if (existing.type !== h.action) existing.type = "MIXED";
            existing.count += 1;
        }
    });
    return Array.from(markersMap.values());
  };

  const totalMarkers = useMemo(() => getMarkers(chartData, false), [chartData, history]);

  return (
    <>
      <TopAppBar />
      <main className="flex flex-col items-center pt-24 pb-32 px-4 md:px-12 z-10 relative gap-8 max-w-[1400px] mx-auto">
        <div className="flex flex-col sm:flex-row justify-between items-center w-full gap-4">
          <h1 className="text-3xl font-display-xl uppercase tracking-widest text-[#f2b98b]">Your Portfolio</h1>
          <div className="flex bg-black/40 p-1 rounded-xl border border-white/10">
            {["1d", "1mo", "1y"].map(r => (
              <button 
                key={r} 
                onClick={() => setTimeRange(r)} 
                className={`px-6 py-2 rounded-lg text-xs font-bold tracking-widest uppercase transition-all ${timeRange === r ? "bg-[#f2b98b] text-black shadow-lg" : "hover:bg-white/10 text-white/50 hover:text-white"}`}
              >
                 {r}
              </button>
            ))}
          </div>
        </div>

        <div className="w-full grid grid-cols-1 lg:grid-cols-3 gap-8">
          {!data ? <p className="text-center opacity-50 col-span-3">Loading...</p> : (
            <>
              {/* Total Portfolio Floating Window */}
              <div className="lg:col-span-2 glass-window p-8 rounded-3xl flex flex-col gap-8 shadow-2xl relative overflow-hidden h-fit">
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
                  <div className="flex flex-col bg-black/40 p-6 rounded-2xl border border-white/5">
                    <span className="text-[10px] uppercase tracking-widest text-secondary font-bold mb-2">Total Value</span>
                    <span className="text-4xl font-bold text-white">${data.summary.total_value.toFixed(2)}</span>
                  </div>
                  <div className="flex flex-col bg-black/40 p-6 rounded-2xl border border-white/5">
                    <span className="text-[10px] uppercase tracking-widest text-secondary font-bold mb-2">Total Profit</span>
                    <span className={`text-3xl font-bold ${data.summary.total_profit >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {data.summary.total_profit >= 0 ? "+" : ""}${data.summary.total_profit.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex flex-col bg-black/40 p-6 rounded-2xl border border-white/5">
                    <span className="text-[10px] uppercase tracking-widest text-secondary font-bold mb-2">Return</span>
                    <span className={`text-3xl font-bold ${data.summary.total_return_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {data.summary.total_return_pct >= 0 ? "+" : ""}{data.summary.total_return_pct.toFixed(2)}%
                    </span>
                  </div>
                </div>

                <div className="w-full h-[400px] relative z-10">
                  {chartData.length === 0 ? null : (
                    <ResponsiveContainer width="100%" height={400} minWidth={0} minHeight={0}>
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f2b98b" stopOpacity={0.4}/>
                            <stop offset="95%" stopColor="#f2b98b" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="date" stroke="rgba(255,255,255,0.2)" fontSize={11} tickLine={false} axisLine={false} />
                        <YAxis domain={["auto", "auto"]} stroke="rgba(255,255,255,0.2)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                        <Tooltip 
                          contentStyle={{ background: "rgba(20,20,22,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px", boxShadow: "0 10px 30px rgba(0,0,0,0.5)" }}
                          itemStyle={{ color: "#f2b98b", fontWeight: "bold" }}
                        />
                        <Area type="monotone" dataKey="value" stroke="#f2b98b" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
                        
                        {totalMarkers.map((m, i) => (
                           <ReferenceDot key={i} x={m.date} y={m.value} r={5} fill={m.type === "BUY" ? "#4ade80" : m.type === "SELL" ? "#f87171" : "#fbbf24"} stroke="#0f0f10" strokeWidth={2}>
                              <title>{m.type} {m.count > 1 ? `(${m.count} orders)` : ""}</title>
                           </ReferenceDot>
                        ))}
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>

              {/* Individual Stocks Windows */}
              <div className="lg:col-span-1 flex flex-col gap-6">
                {data.portfolio.length === 0 && (
                   <div className="glass-panel p-8 rounded-3xl text-center opacity-50 flex flex-col items-center justify-center h-full border border-white/5">
                      <span className="material-symbols-outlined text-4xl mb-2">account_balance</span>
                      <p>No active positions.</p>
                   </div>
                )}
                {data.portfolio.map((pos: any, i: number) => {
                  const stockChart = individualCharts[pos.ticker] || [];
                  const stockMarkers = getMarkers(stockChart, true, pos.ticker);
                  
                  return (
                  <div key={i} className="glass-window p-6 rounded-3xl flex flex-col gap-4 shadow-xl border border-white/10 hover:border-white/20 transition-all">
                    <div className="flex justify-between items-start">
                      <div className="flex flex-col">
                        <span className="text-2xl font-bold flex items-center gap-2">
                           {pos.ticker}
                           {pos.shares > 0 && (
                             <button onClick={() => handleSell(pos.ticker)} className="px-2 py-1 bg-red-500/20 text-red-400 text-[10px] rounded hover:bg-red-500/40 transition-colors uppercase tracking-widest font-bold ml-2">Sell</button>
                           )}
                        </span>
                        <span className="text-[11px] uppercase tracking-widest text-secondary mt-1 flex flex-col gap-1">
                          <span>{pos.shares} Shares</span>
                          {pos.shares > 0 ? (
                            <span className="text-green-400">Bought At: ${pos.buy_price.toFixed(2)}</span>
                          ) : (
                            <span className="text-red-400">Sold At: ${(history.find(h => h.ticker === pos.ticker && h.action === "SELL")?.price || pos.current_price).toFixed(2)}</span>
                          )}
                        </span>
                      </div>
                      <div className="flex flex-col text-right">
                        <span className="text-xl font-bold text-white">${pos.current_price.toFixed(2)}</span>
                        <span className={`text-xs font-bold mt-1 px-2 py-1 rounded-md ${pos.return_pct >= 0 ? "bg-green-400/10 text-green-400" : "bg-red-400/10 text-red-400"}`}>
                          {pos.return_pct >= 0 ? "+" : ""}{pos.return_pct.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                    
                    <div className="w-full h-[120px] mt-2">
                      {stockChart.length === 0 ? null : (
                        <ResponsiveContainer width="100%" height={120} minWidth={0} minHeight={0}>
                          <AreaChart data={stockChart}>
                            <defs>
                              <linearGradient id={`color-${pos.ticker}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={pos.return_pct >= 0 ? "#4ade80" : "#f87171"} stopOpacity={0.3}/>
                                <stop offset="95%" stopColor={pos.return_pct >= 0 ? "#4ade80" : "#f87171"} stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <XAxis dataKey="date" hide={true} />
                            <YAxis 
                              domain={[
                                dataMin => pos.threshold && !isNaN(parseFloat(pos.threshold.replace("$", "").replace("±", "").replace("+", "").replace("-", ""))) ? Math.min(dataMin, pos.buy_price - parseFloat(pos.threshold.replace("$", "").replace("±", "").replace("+", "").replace("-", ""))) : dataMin,
                                dataMax => pos.threshold && !isNaN(parseFloat(pos.threshold.replace("$", "").replace("±", "").replace("+", "").replace("-", ""))) ? Math.max(dataMax, pos.buy_price + parseFloat(pos.threshold.replace("$", "").replace("±", "").replace("+", "").replace("-", ""))) : dataMax
                              ]} 
                              hide={true} 
                            />
                            <Tooltip 
                              contentStyle={{ background: "rgba(20,20,22,0.95)", border: "none", borderRadius: "8px", fontSize: "12px" }}
                              itemStyle={{ color: pos.return_pct >= 0 ? "#4ade80" : "#f87171" }}
                            />
                            <Area type="monotone" dataKey="value" stroke={pos.return_pct >= 0 ? "#4ade80" : "#f87171"} strokeWidth={2} fillOpacity={1} fill={`url(#color-${pos.ticker})`} />
                            {stockMarkers.map((m, i) => (
                               <ReferenceDot key={i} x={m.date} y={m.value} r={4} fill={m.type === "BUY" ? "#4ade80" : m.type === "SELL" ? "#f87171" : "#fbbf24"} stroke="#0f0f10" strokeWidth={1} />
                            ))}
                            {pos.threshold && !isNaN(parseFloat(pos.threshold.replace("$", "").replace("±", "").replace("+", "").replace("-", ""))) && (
                               <>
                                 <ReferenceLine y={pos.buy_price + parseFloat(pos.threshold.replace("$", "").replace("±", "").replace("+", "").replace("-", ""))} stroke="#8884d8" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: `+ Threshold`, fill: '#8884d8', fontSize: 10 }} />
                                 <ReferenceLine y={pos.buy_price - parseFloat(pos.threshold.replace("$", "").replace("±", "").replace("+", "").replace("-", ""))} stroke="#8884d8" strokeDasharray="3 3" label={{ position: 'insideBottomLeft', value: `- Threshold`, fill: '#8884d8', fontSize: 10 }} />
                               </>
                            )}
                          </AreaChart>
                        </ResponsiveContainer>
                      )}
                    </div>
                  </div>
                )})}
              </div>
            </>
          )}
        </div>
      </main>
    </>
  );
}
