"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface Ticker {
  ticker: string;
  name: string;
  exchange: string;
  sector: string;
}

interface TickerSearchProps {
  onSelect: (ticker: Ticker) => void;
  onClear: () => void;
  selectedTicker: Ticker | null;
  disabled?: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function TickerSearch({
  onSelect,
  onClear,
  selectedTicker,
  disabled,
}: TickerSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Ticker[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [price, setPrice] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Fetch search results
  const searchTickers = useCallback(async (q: string) => {
    try {
      const resp = await fetch(`${API_BASE}/api/tickers/search?q=${encodeURIComponent(q)}&limit=8`);
      if (resp.ok) {
        const data = await resp.json();
        setResults(data);
      }
    } catch {
      // Fallback: use empty results on network error
      setResults([]);
    }
  }, []);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!query || query.length < 1) {
      searchTickers(""); // Load defaults
      return;
    }

    debounceRef.current = setTimeout(() => {
      searchTickers(query);
    }, 150);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, searchTickers]);

  // Fetch price when ticker is selected
  useEffect(() => {
    if (!selectedTicker) {
      setPrice(null);
      return;
    }

    const fetchPrice = async () => {
      try {
        const resp = await fetch(`${API_BASE}/api/tickers/${selectedTicker.ticker}/price`);
        if (resp.ok) {
          const data = await resp.json();
          if (data.price) {
            setPrice(`$${data.price.toFixed(2)}`);
          }
        }
      } catch {
        setPrice(null);
      }
    };

    fetchPrice();
  }, [selectedTicker]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((prev) => Math.min(prev + 1, results.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((prev) => Math.max(prev - 1, 0));
        break;
      case "Enter":
        e.preventDefault();
        if (activeIndex >= 0 && results[activeIndex]) {
          handleSelect(results[activeIndex]);
        }
        break;
      case "Escape":
        setIsOpen(false);
        break;
    }
  };

  const handleSelect = (ticker: Ticker) => {
    onSelect(ticker);
    setIsOpen(false);
    setQuery("");
    setActiveIndex(-1);
  };

  // Show selected ticker view
  if (selectedTicker) {
    return (
      <div className="ticker-selected">
        <div className="ticker-selected-info">
          <span className="ticker-selected-symbol">{selectedTicker.ticker}</span>
          <span className="ticker-selected-name">{selectedTicker.name}</span>
        </div>
        {price && <span className="ticker-selected-price">{price}</span>}
        <button
          className="ticker-clear-btn"
          onClick={onClear}
          disabled={disabled}
          aria-label="Clear ticker"
        >
          ✕
        </button>
      </div>
    );
  }

  return (
    <div className="ticker-search-container">
      <div className="ticker-search-input-wrapper">
        <span className="ticker-search-icon">🔍</span>
        <input
          ref={inputRef}
          type="text"
          className="ticker-search-input"
          placeholder="Search ticker or company (e.g., NVDA, Nvidia)..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setActiveIndex(-1);
            if (!isOpen) setIsOpen(true);
          }}
          onFocus={() => {
            setIsOpen(true);
            if (!query) searchTickers("");
          }}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          id="ticker-search"
          autoComplete="off"
        />
      </div>

      {isOpen && results.length > 0 && (
        <div className="ticker-dropdown" ref={dropdownRef}>
          {results.map((ticker, index) => (
            <div
              key={ticker.ticker}
              className={`ticker-dropdown-item ${index === activeIndex ? "active" : ""}`}
              onClick={() => handleSelect(ticker)}
              onMouseEnter={() => setActiveIndex(index)}
            >
              <div className="ticker-dropdown-item-left">
                <span className="ticker-symbol">{ticker.ticker}</span>
                <span className="ticker-name">{ticker.name}</span>
              </div>
              <span
                className={`ticker-exchange-badge ${ticker.exchange.toLowerCase()}`}
              >
                {ticker.exchange}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
