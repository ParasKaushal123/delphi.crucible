"use client";
import { useEffect, useState } from "react";
import TopAppBar from "../components/TopAppBar";
import ReactMarkdown from "react-markdown";

export default function HistoryPage() {
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${API_BASE}/api/history`)
      .then(res => res.json())
      .then(data => setHistory(data.history || []))
      .catch(console.error);
  }, []);

  return (
    <>
      <TopAppBar />
      <main className="flex flex-col items-center pt-24 pb-32 px-12 z-10 relative gap-8">
        <h1 className="text-3xl font-display-xl uppercase tracking-widest text-[#f2b98b]">Investment History</h1>
        <div className="w-full max-w-4xl flex flex-col gap-4">
          {history.length === 0 && <p className="text-on-surface-variant opacity-50 text-center">No history yet.</p>}
          {history.map((item, i) => (
            <div key={i} className="glass-panel p-6 rounded-2xl flex flex-col gap-2">
              <span className="text-xs text-on-surface-variant">{item.timestamp}</span>
              {item.type === "transaction" ? (
                <div className="text-lg">
                  {item.action === "BUY" || item.action === "ADD" ? <span className="text-green-400 font-bold">BOUGHT</span> : item.action === "SELL" ? <span className="text-red-400 font-bold">SOLD</span> : item.action === "ALERT" ? <span className="text-yellow-400 font-bold tracking-widest uppercase text-sm mr-2">⚠️ Threshold Crossed</span> : <span className="text-blue-400">{item.action}</span>} 
                  {' '}{item.action === "ALERT" ? "for" : `${item.shares} shares of`} <span className="font-bold text-white uppercase">{item.ticker}</span> 
                  {item.price && ` at $${item.price.toFixed(2)}`}
                </div>
              ) : (
                <div className="prose prose-sm prose-invert max-w-none">
                  <h3 className="text-secondary">Delphi Memo: {item.ticker}</h3>
                  <ReactMarkdown>{item.memo}</ReactMarkdown>
                </div>
              )}
            </div>
          ))}
        </div>
      </main>
    </>
  );
}
