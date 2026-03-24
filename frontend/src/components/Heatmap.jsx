import React, { useState, useEffect } from 'react';
import axios from 'axios';
import clsx from 'clsx';
import { RefreshCw, AlertCircle } from 'lucide-react';

const SECTOR_COLORS = {
  Banking: '#3b82f6',
  IT: '#8b5cf6',
  Energy: '#f59e0b',
  FMCG: '#10b981',
  Finance: '#06b6d4',
  Telecom: '#6366f1',
  Auto: '#f97316',
  Pharma: '#ec4899',
  Metals: '#9ca3af',
  Infra: '#84cc16',
  'Consumer': '#a78bfa',
  Materials: '#78716c',
  Utilities: '#22d3ee',
  Conglomerate: '#fb923c',
  Renewables: '#4ade80',
  Insurance: '#f472b6',
  Agri: '#a3e635',
  Healthcare: '#34d399',
};

function getTileColor(score) {
  if (score > 0.4)  return { bg: '#14532d', border: '#16a34a', text: '#4ade80' };
  if (score > 0.15) return { bg: '#166534', border: '#22c55e', text: '#86efac' };
  if (score > 0)    return { bg: '#1a2e1a', border: '#4ade80', text: '#bbf7d0' };
  if (score === 0)  return { bg: '#1c1c1c', border: '#374151', text: '#9ca3af' };
  if (score > -0.15) return { bg: '#2e1a1a', border: '#ef4444', text: '#fca5a5' };
  if (score > -0.4)  return { bg: '#7f1d1d', border: '#dc2626', text: '#fca5a5' };
  return             { bg: '#450a0a', border: '#b91c1c', text: '#f87171' };
}

export default function Heatmap({ onNavigateToAnalysis }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fetchedAt, setFetchedAt] = useState(null);
  const [filterSector, setFilterSector] = useState('All');

  const [fiiDii, setFiiDii] = useState(null);

  const fetchHeatmap = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get('http://localhost:8000/api/heatmap');
      setData(res.data.heatmap);
      setFetchedAt(res.data.fetched_at);
      setFiiDii(res.data.fiiDii || null);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load heatmap.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchHeatmap(); }, []);

  const sectors = data
    ? ['All', ...Array.from(new Set(data.map(d => d.sector))).sort()]
    : ['All'];

  const filtered = data
    ? (filterSector === 'All' ? data : data.filter(d => d.sector === filterSector))
    : [];

  if (loading) return (
    <div className="text-center py-24 text-gray-500 font-mono animate-pulse">
      FETCHING NIFTY50 SENTIMENT DATA…<br/>
      <span className="text-xs text-gray-600">This may take a minute (running FinBERT on 50 stocks)</span>
    </div>
  );

  if (error) return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-[#161212] border border-red-900/50 rounded-md flex items-start gap-4 mt-8">
      <AlertCircle className="text-red-500 mt-1" size={24} />
      <div>
        <h3 className="text-lg font-semibold text-red-500 mb-1">Heatmap Error</h3>
        <p className="text-gray-300 font-mono text-sm">{error}</p>
      </div>
    </div>
  );

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-100 tracking-tight">Nifty50 Sentiment Heatmap</h2>
          {fetchedAt && (
            <p className="text-xs font-mono text-gray-500 mt-1">
              Data as of {new Date(fetchedAt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} · Cached for 30 min
            </p>
          )}
        </div>
        <button
          onClick={fetchHeatmap}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-xs font-mono text-gray-300 hover:bg-gray-700 transition-colors"
        >
          <RefreshCw size={13} />
          Refresh
        </button>
      </div>

      {/* Feature 6: FII/DII on Heatmap */}
      {fiiDii && fiiDii.fii && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <div className="bg-[#121212] border border-gray-800 rounded-md p-4">
            <p className="text-[10px] font-mono text-gray-600 uppercase">FII Net</p>
            <p className={clsx("text-lg font-mono font-bold", fiiDii.fiiFlow === 'IN' ? 'text-green-400' : 'text-red-400')}>
              {fiiDii.fiiFlow === 'IN' ? '🟢' : '🔴'} {typeof fiiDii.fii.netValue === 'number' ? `₹${(fiiDii.fii.netValue / 100).toFixed(0)}Cr` : fiiDii.fii.netValue}
            </p>
            <p className="text-[9px] font-mono text-gray-600 mt-0.5">Foreign Money Flowing {fiiDii.fiiFlow}</p>
          </div>
          <div className="bg-[#121212] border border-gray-800 rounded-md p-4">
            <p className="text-[10px] font-mono text-gray-600 uppercase">DII Net</p>
            <p className="text-lg font-mono font-bold text-blue-400">
              {typeof fiiDii.dii?.netValue === 'number' ? `₹${(fiiDii.dii.netValue / 100).toFixed(0)}Cr` : fiiDii.dii?.netValue || '—'}
            </p>
          </div>
          {fiiDii.date && (
            <div className="bg-[#121212] border border-gray-800 rounded-md p-4 flex items-center">
              <p className="text-[10px] font-mono text-gray-600">Date: {fiiDii.date}</p>
            </div>
          )}
        </div>
      )}

      {/* Sector filter */}
      <div className="flex flex-wrap gap-2">
        {sectors.map(s => (
          <button
            key={s}
            onClick={() => setFilterSector(s)}
            className={clsx(
              'px-3 py-1 text-xs font-mono rounded-full border transition-colors',
              filterSector === s
                ? 'bg-blue-600 border-blue-500 text-white'
                : 'bg-[#161616] border-gray-800 text-gray-400 hover:border-gray-600'
            )}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs font-mono text-gray-500">
        <span>Bearish</span>
        <div className="flex gap-1">
          {['#7f1d1d','#b91c1c','#374151','#166534','#14532d'].map(c => (
            <div key={c} className="w-6 h-3 rounded-sm" style={{ backgroundColor: c }} />
          ))}
        </div>
        <span>Bullish</span>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {filtered.map((stock) => {
          const col = getTileColor(stock.sentiment_score);
          const sectorColor = SECTOR_COLORS[stock.sector] || '#6b7280';
          return (
            <div
              key={stock.ticker}
              onClick={onNavigateToAnalysis ? () => onNavigateToAnalysis(stock.ticker) : undefined}
              className="rounded-md p-3 border transition-all duration-200 hover:scale-[1.03] hover:shadow-[0_0_15px_rgba(59,130,246,0.3)] hover:border-blue-400 hover:z-20 cursor-pointer relative"
              style={{ backgroundColor: col.bg, borderColor: col.border }}
            >
              <div className="text-[10px] font-mono px-1.5 py-0.5 rounded-sm w-fit mb-1"
                   style={{ backgroundColor: sectorColor + '33', color: sectorColor }}>
                {stock.sector}
              </div>
              <div className="text-sm font-bold text-gray-100 truncate">{stock.ticker}</div>
              <div className="text-[10px] text-gray-400 truncate mb-2">{stock.name}</div>
              <div className="text-lg font-mono font-bold" style={{ color: col.text }}>
                {stock.sentiment_score > 0 ? '+' : ''}{(stock.sentiment_score * 100).toFixed(1)}
              </div>
              <div className="text-[9px] text-gray-600 font-mono">{stock.overall || '—'}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
