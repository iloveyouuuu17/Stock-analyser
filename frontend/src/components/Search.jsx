import React, { useState } from 'react';
import { SearchIcon, TrendingUp } from 'lucide-react';

const TRENDING_STOCKS = ['NIFTY 50', 'SENSEX', 'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'TATAMOTORS'];

export default function Search({ onSearch, isLoading }) {
  const [ticker, setTicker] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (ticker.trim()) {
      onSearch(ticker.toUpperCase().trim());
    }
  };

  const handleChipClick = (stock) => {
    setTicker(stock);
    onSearch(stock);
  };

  return (
    <div className="w-full max-w-4xl mx-auto mb-8">
      <form onSubmit={handleSubmit} className="relative mb-6">
        <div className="flex items-center bg-[#1e1e1e] border border-gray-800 rounded-md overflow-hidden focus-within:border-blue-500 transition-colors shadow-black/50 shadow-lg">
          <div className="pl-4 text-gray-400">
            <SearchIcon size={20} />
          </div>
          <input
            type="text"
            className="w-full bg-transparent px-4 py-4 text-xl font-mono text-gray-100 placeholder-gray-600 focus:outline-none uppercase"
            placeholder="ENTER NSE TICKER OR INDEX (E.G., NIFTY 50, RELIANCE)"
            value={ticker}
            onChange={(e) => {
              // The native input event contains the full current string.
              // Just set it directly, do not append.
              setTicker(e.target.value);
            }}
            disabled={isLoading}
            autoComplete="off"
            spellCheck="false"
            autoFocus
          />
          <button
            type="submit"
            disabled={isLoading || !ticker.trim()}
            className="px-8 py-4 bg-gray-800 hover:bg-gray-700 text-sm font-semibold tracking-wider text-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed border-l border-gray-800 uppercase"
          >
            {isLoading ? 'ANALYZING...' : 'ANALYZE'}
          </button>
        </div>
      </form>

      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div className="flex items-center text-xs font-semibold text-gray-500 uppercase tracking-widest gap-1">
          <TrendingUp size={14} />
          Trending
        </div>
        <div className="flex flex-wrap gap-2">
          {TRENDING_STOCKS.map((stock) => (
            <button
              key={stock}
              onClick={() => handleChipClick(stock)}
              disabled={isLoading}
              className="px-3 py-1 text-xs font-mono font-medium text-gray-300 bg-[#161616] border border-gray-800 rounded-full hover:bg-gray-800 hover:text-white transition-colors disabled:opacity-50"
            >
              {stock}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
