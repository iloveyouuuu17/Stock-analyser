import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import clsx from 'clsx';
import { Star, RefreshCw, Bell, Trash2, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

const STORAGE_KEY = 'issa_watchlist';
const SCORES_KEY  = 'issa_watchlist_scores';

function loadWatchlist() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
  catch { return []; }
}
function saveWatchlist(list) { localStorage.setItem(STORAGE_KEY, JSON.stringify(list)); }

function loadLastScores() {
  try { return JSON.parse(localStorage.getItem(SCORES_KEY) || '{}'); }
  catch { return {}; }
}
function saveLastScores(scores) { localStorage.setItem(SCORES_KEY, JSON.stringify(scores)); }

export default function Watchlist() {
  const [tickers, setTickers]       = useState(loadWatchlist);
  const [data, setData]             = useState(null);
  const [loading, setLoading]       = useState(false);
  const [addInput, setAddInput]     = useState('');
  const [lastScores, setLastScores] = useState(loadLastScores);

  const refresh = useCallback(async () => {
    if (tickers.length === 0) return;
    setLoading(true);
    try {
      const res = await axios.get('http://localhost:8000/api/watchlist/refresh', {
        params: { tickers: tickers.join(',') }
      });
      setData(res.data.stocks);

      // Check for significant shifts
      const prev = loadLastScores();
      const newScores = {};
      (res.data.stocks || []).forEach(s => {
        newScores[s.ticker] = s.score || 0;
      });
      saveLastScores(newScores);
      setLastScores(prev); // keep previous for comparison
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [tickers]);

  // Auto-refresh every 30 minutes
  useEffect(() => {
    if (tickers.length > 0) refresh();
    const interval = setInterval(refresh, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, [tickers, refresh]);

  const addTicker = () => {
    const t = addInput.trim().toUpperCase();
    if (t && !tickers.includes(t)) {
      const updated = [...tickers, t];
      setTickers(updated);
      saveWatchlist(updated);
      setAddInput('');
    }
  };

  const removeTicker = (t) => {
    const updated = tickers.filter(x => x !== t);
    setTickers(updated);
    saveWatchlist(updated);
    if (data) setData(data.filter(s => s.ticker !== t));
  };

  const hasShift = (ticker, score) => {
    const prev = lastScores[ticker];
    if (prev === undefined) return false;
    return Math.abs((score || 0) - prev) > 0.2;
  };

  const VerdictIcon = (o) => o === 'Bullish' ? ArrowUpRight : o === 'Bearish' ? ArrowDownRight : Minus;
  const vcol = (o) => o === 'Bullish' ? 'text-green-400' : o === 'Bearish' ? 'text-red-400' : 'text-gray-500';

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-100 tracking-tight flex items-center gap-2">
            <Star size={20} className="text-yellow-400" />
            Watchlist
          </h2>
          <p className="text-xs font-mono text-gray-500 mt-1">Auto-refreshes every 30 minutes · Stored locally</p>
        </div>
        <button onClick={refresh} disabled={loading || tickers.length === 0}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-xs font-mono text-gray-300 hover:bg-gray-700 transition-colors disabled:opacity-50">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {/* Add ticker input */}
      <form onSubmit={(e) => { e.preventDefault(); addTicker(); }} className="flex gap-3">
        <input type="text" value={addInput} onChange={e => setAddInput(e.target.value)}
          placeholder="Add ticker (e.g. INFY)" disabled={loading}
          className="flex-1 bg-[#1e1e1e] border border-gray-800 rounded-md px-4 py-3 text-gray-100 font-mono text-sm uppercase placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
        />
        <button type="submit" disabled={!addInput.trim()}
          className="px-6 py-3 bg-yellow-600 hover:bg-yellow-500 rounded-md text-sm font-semibold text-white transition-colors disabled:opacity-50">
          ★ Add
        </button>
      </form>

      {tickers.length === 0 && (
        <div className="text-center py-16 text-gray-600 font-mono text-sm">
          No stocks in watchlist. Add some tickers above to track their sentiment.
        </div>
      )}

      {/* Stock cards */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {data.map(s => {
            const Icon = VerdictIcon(s.overall);
            const shifted = hasShift(s.ticker, s.score);
            return (
              <div key={s.ticker} className={clsx(
                "bg-[#121212] border rounded-md p-4 relative",
                shifted ? 'border-amber-600/60' : 'border-gray-800'
              )}>
                {shifted && (
                  <div className="absolute -top-2 -right-2 bg-amber-600 rounded-full p-1" title="Sentiment shifted significantly">
                    <Bell size={12} className="text-white" />
                  </div>
                )}
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <p className="text-sm font-bold text-gray-100 font-mono">{s.ticker}</p>
                    <p className="text-xs text-gray-500 truncate">{s.company || s.ticker}</p>
                  </div>
                  <button onClick={() => removeTicker(s.ticker)} className="text-gray-700 hover:text-red-400 transition-colors">
                    <Trash2 size={14} />
                  </button>
                </div>
                {s.error ? (
                  <p className="text-xs text-red-400">{s.error}</p>
                ) : (
                  <>
                    {s.price && (
                      <p className="text-lg font-mono font-bold text-gray-200 mb-1">
                        ₹{s.price.toFixed(2)}
                        <span className={clsx("text-xs ml-2", s.changePct >= 0 ? 'text-green-400' : 'text-red-400')}>
                          {s.changePct >= 0 ? '+' : ''}{s.changePct?.toFixed(2)}%
                        </span>
                      </p>
                    )}
                    <div className={clsx('flex items-center gap-1 text-xs font-mono font-bold mt-1', vcol(s.overall))}>
                      <Icon size={14} />
                      {s.overall}
                      <span className="text-gray-600 ml-1">({s.score >= 0 ? '+' : ''}{(s.score * 100).toFixed(1)})</span>
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Export for use in other components
export function addToWatchlist(ticker) {
  const list = loadWatchlist();
  const t = ticker.toUpperCase();
  if (!list.includes(t)) {
    list.push(t);
    saveWatchlist(list);
  }
}
