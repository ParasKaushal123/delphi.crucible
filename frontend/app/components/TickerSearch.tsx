"use client";

import { useState, useEffect, useRef } from "react";

interface Ticker {
  ticker: string;
  name: string;
  exchange: string;
  sector: string;
}

const COMMON_TICKERS: Ticker[] = [
  { ticker: "NVDA", name: "NVIDIA Corp.", exchange: "NASDAQ", sector: "Technology" },
  { ticker: "MSFT", name: "Microsoft Corp.", exchange: "NASDAQ", sector: "Technology" },
  { ticker: "AAPL", name: "Apple Inc.", exchange: "NASDAQ", sector: "Technology" },
  { ticker: "TSLA", name: "Tesla Inc.", exchange: "NASDAQ", sector: "Consumer Cyclical" },
  { ticker: "JPM", name: "JPMorgan Chase", exchange: "NYSE", sector: "Financial Services" },
  { ticker: "GS", name: "Goldman Sachs", exchange: "NYSE", sector: "Financial Services" },
  { ticker: "LLY", name: "Eli Lilly & Co.", exchange: "NYSE", sector: "Healthcare" },
  { ticker: "UNH", name: "UnitedHealth", exchange: "NYSE", sector: "Healthcare" },
];

interface Props {
  onSelect: (ticker: Ticker) => void;
  onClear?: () => void;
  selectedTicker?: Ticker | null;
  disabled?: boolean;
}

export default function TickerSearch({ onSelect, onClear, selectedTicker, disabled }: Props) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const filtered = query
    ? COMMON_TICKERS.filter((t) =>
        t.ticker.toLowerCase().includes(query.toLowerCase()) ||
        t.name.toLowerCase().includes(query.toLowerCase())
      )
    : COMMON_TICKERS;

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (selectedTicker) {
    return (
      <div className="relative border border-secondary/30 rounded-lg p-3 bg-surface-container/30 flex justify-between items-center">
        <div className="flex flex-col">
          <span className="font-headline-md text-secondary font-bold text-lg">{selectedTicker.ticker}</span>
          <span className="font-label-sm text-on-surface-variant text-xs">{selectedTicker.name}</span>
        </div>
        <button
          onClick={onClear}
          disabled={disabled}
          className="text-on-surface-variant hover:text-error transition-colors p-1"
        >
          <span className="material-symbols-outlined text-sm">close</span>
        </button>
      </div>
    );
  }

  return (
    <div ref={wrapperRef} className="relative z-50">
      <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">search</span>
      <input
        type="text"
        className="w-full bg-surface-container/50 border-0 border-b border-white/10 text-primary placeholder-on-surface-variant focus:ring-0 focus:border-secondary transition-colors pl-9 py-2 font-label-sm text-sm rounded-t-lg outline-none"
        placeholder="Search ticker..."
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        disabled={disabled}
      />
      
      {isOpen && (
        <div className="absolute top-full left-0 w-full mt-1 bg-surface-container-high border border-white/10 rounded-lg shadow-xl overflow-hidden max-h-60 overflow-y-auto">
          {filtered.length > 0 ? (
            filtered.map((t) => (
              <div
                key={t.ticker}
                className="px-4 py-3 hover:bg-white/5 cursor-pointer flex justify-between items-center border-b border-white/5 last:border-0"
                onClick={() => {
                  onSelect(t);
                  setIsOpen(false);
                  setQuery("");
                }}
              >
                <div className="flex flex-col">
                  <span className="text-primary font-bold font-label-sm">{t.ticker}</span>
                  <span className="text-on-surface-variant text-xs font-body-md">{t.name}</span>
                </div>
                <span className="text-secondary text-[10px] uppercase font-eyebrow tracking-wider border border-secondary/30 px-1.5 py-0.5 rounded">
                  {t.exchange}
                </span>
              </div>
            ))
          ) : (
            <div className="px-4 py-3 text-on-surface-variant text-sm text-center">No tickers found.</div>
          )}
        </div>
      )}
    </div>
  );
}
