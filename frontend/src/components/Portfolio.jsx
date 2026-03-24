import React, { useState } from 'react';
import axios from 'axios';
import clsx from 'clsx';
import { ArrowUpRight, ArrowDownRight, Minus, AlertCircle, Loader2 } from 'lucide-react';

function ScoreBar({ score }) {
  const pct = Math.abs(score) * 100;
  const isPos = score >= 0;
  return (
    <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden mt-1">
      <div
        className="h-full rounded-full transition-all"
        style={{
          width: `${Math.min(pct, 100)}%`,
          backgroundColor: isPos ? '#22c55e' : '#ef4444'
        }}
      />
    </div>
  );
}

export default function Portfolio() {
  const [input, setInput] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await axios.get('http://localhost:8000/api/portfolio', {
        params: { tickers: input.trim() }
      });
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch portfolio data.');
    } finally {
      setLoading(false);
    }
  };

  const verdictColor = (v) =>
    v === 'Bullish' ? 'text-green-400' :
    v === 'Bearish' ? 'text-red-400' : 'text-gray-400';

  const VerdictIcon = (v) =>
    v === 'Bullish' ? ArrowUpRight : v === 'Bearish' ? ArrowDownRight : Minus;

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-100 tracking-tight">Portfolio Sentiment Score</h2>
        <p className="text-xs font-mono text-gray-500 mt-1">Enter comma-separated NSE tickers to analyse your portfolio</p>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="E.g. RELIANCE, TCS, INFY, HDFCBANK"
          disabled={loading}
          className="flex-1 bg-[#1e1e1e] border border-gray-800 rounded-md px-4 py-3 text-gray-100 font-mono text-sm uppercase placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-md text-sm font-semibold text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? <><Loader2 size={16} className="animate-spin" /> Analysing…</> : 'Analyse →'}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="p-4 bg-[#161212] border border-red-900/50 rounded-md flex items-start gap-3">
          <AlertCircle className="text-red-500 mt-0.5" size={18} />
          <p className="text-sm font-mono text-gray-300">{error}</p>
        </div>
      )}

      {/* Results */}
      {data && (
        <div className="space-y-6">
          {/* Portfolio verdict card */}
          <div className="bg-[#121212] border border-gray-800 rounded-md p-6 flex items-center justify-between">
            <div>
              <p className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-1">Portfolio Verdict</p>
              <div className={clsx('text-4xl font-bold uppercase flex items-center gap-2', verdictColor(data.portfolioVerdict))}>
                {React.createElement(VerdictIcon(data.portfolioVerdict), { size: 32 })}
                {data.portfolioVerdict}
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs font-mono text-gray-500 mb-1">Weighted Score</p>
              <span className={clsx('text-3xl font-mono font-bold', data.portfolioScore >= 0 ? 'text-green-400' : 'text-red-400')}>
                {data.portfolioScore > 0 ? '+' : ''}{(data.portfolioScore * 100).toFixed(1)}
              </span>
            </div>
          </div>

          {/* Per-stock cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {data.stocks.map(s => {
              const Icon = VerdictIcon(s.overall);
              return (
                <div key={s.ticker} className="bg-[#121212] border border-gray-800 rounded-md p-4">
                  {s.error ? (
                    <div>
                      <p className="text-sm font-bold text-gray-200 font-mono">{s.ticker}</p>
                      <p className="text-xs text-red-400 mt-1">{s.error}</p>
                    </div>
                  ) : (
                    <>
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <p className="text-sm font-bold text-gray-100 font-mono">{s.ticker}</p>
                          <p className="text-xs text-gray-500 truncate">{s.company}</p>
                        </div>
                        <div className={clsx('flex items-center gap-1 text-xs font-mono font-bold', verdictColor(s.overall))}>
                          <Icon size={14} />
                          {s.overall}
                        </div>
                      </div>
                      <div className={clsx('text-xl font-mono font-bold', s.score >= 0 ? 'text-green-400' : 'text-red-400')}>
                        {s.score >= 0 ? '+' : ''}{(s.score * 100).toFixed(1)}
                      </div>
                      <ScoreBar score={s.score} />
                      <div className="flex gap-3 mt-3 text-xs font-mono text-gray-600">
                        <span className="text-green-500">+{s.positive}</span>
                        <span className="text-gray-500">{s.neutral}</span>
                        <span className="text-red-500">-{s.negative}</span>
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
