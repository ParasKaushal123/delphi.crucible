import { useState, useEffect } from "react";
import { toast } from "react-hot-toast";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface InvestModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTicker?: string;
  initialAmount?: number;
  initialThreshold?: string;
}

export default function InvestModal({ isOpen, onClose, initialTicker = "", initialAmount = 1000, initialThreshold = "" }: InvestModalProps) {
  const [ticker, setTicker] = useState(initialTicker);
  const [amount, setAmount] = useState(initialAmount);
  const [threshold, setThreshold] = useState(initialThreshold);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setTicker(initialTicker);
      setAmount(initialAmount);
      setThreshold(initialThreshold);
    }
  }, [isOpen, initialTicker, initialAmount, initialThreshold]);

  const handleInvest = async () => {
    if (!ticker) return;
    setLoading(true);
    try {
      // Calculate arbitrary shares for paper trading backend that expects shares
      const shares = Math.max(1, Math.floor(amount / 100));
      const resp = await fetch(`${API_BASE}/api/portfolio/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: ticker.toUpperCase(), shares, threshold })
      });
      if (!resp.ok) {
        const data = await resp.json();
        throw new Error(data.detail || "Failed to invest");
      }
      toast.success(`Successfully executed trade order for ${ticker.toUpperCase()} with a threshold of ${threshold}!`);
      onClose();
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center w-screen h-screen bg-[#0f0f10]/80 backdrop-blur-md p-4">
      <div className="w-full sm:w-[450px] min-w-[320px] p-8 rounded-[24px] flex flex-col gap-6 shrink-0" style={{
        background: "rgba(20, 20, 22, 0.95)",
        border: "1px solid rgba(255, 255, 255, 0.1)",
        boxShadow: "inset 0 1px 0 0 rgba(255, 255, 255, 0.05), 0 25px 50px -12px rgba(0, 0, 0, 0.5)",
      }}>
        <h2 className="text-2xl font-display-xl uppercase tracking-widest text-green-400">Execute Order</h2>
        <p className="text-sm text-on-surface-variant font-body-md">
          Review your trade details before submitting the paper trade order to the exchange.
        </p>

        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-xs font-eyebrow tracking-widest text-secondary uppercase">Ticker Symbol</label>
            <input 
              type="text" 
              placeholder="e.g. AAPL"
              value={ticker}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              className="bg-surface/50 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-green-500/50 transition-colors"
            />
          </div>
          <div className="flex gap-4">
            <div className="flex flex-col gap-2 flex-1">
              <label className="text-xs font-eyebrow tracking-widest text-secondary uppercase">Amount ($)</label>
              <input 
                type="number" 
                min="1"
                value={amount}
                onChange={e => setAmount(Number(e.target.value))}
                className="bg-surface/50 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-green-500/50 transition-colors w-full"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-xs font-eyebrow tracking-widest text-secondary uppercase">Threshold Deviation ($)</label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/50">±$</span>
                <input 
                  type="number"
                  value={threshold.replace("$", "").replace("±", "").replace("+", "").replace("-", "")}
                  onChange={e => setThreshold(`$${e.target.value}`)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white placeholder-white/30 focus:outline-none focus:border-[#f2b98b] transition-colors"
                  placeholder="10.00"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-4">
          <button onClick={onClose} className="px-4 py-2 text-on-surface-variant hover:text-white transition-colors text-sm uppercase tracking-wider font-label-sm">
            Cancel
          </button>
          <button 
            onClick={handleInvest} 
            disabled={loading || !ticker || amount <= 0}
            className="px-6 py-3 bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-green-300 border border-green-500/50 font-bold uppercase tracking-widest rounded-xl hover:from-green-500/30 hover:to-emerald-500/30 transition-all text-sm disabled:opacity-50 shadow-[0_0_15px_rgba(34,197,94,0.2)]"
          >
            {loading ? "Executing..." : "Submit Order"}
          </button>
        </div>
      </div>
    </div>
  );
}
