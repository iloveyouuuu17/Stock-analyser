import React, { useState } from 'react';
import axios from 'axios';
import { Sparkles, ArrowRight, AlertTriangle, ShieldCheck, Target, Info, Loader2 } from 'lucide-react';
import clsx from 'clsx';

export default function StrategyLab() {
  const [ticker, setTicker] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!ticker.trim() || !query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await axios.post('http://localhost:8000/api/strategy/simulate', {
        ticker: ticker.toUpperCase().trim(),
        query: query.trim()
      });
      setResult(res.data);
    } catch (err) {
      if (err.response) {
        setError(err.response.data.detail || 'Server Error');
      } else {
        setError('Network Error: Could not connect to the backend.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getRecColor = (rec) => {
    const r = (rec || '').toUpperCase();
    if (r === 'BUY') return 'text-green-400 bg-green-900/30 border-green-700/50';
    if (r === 'SELL') return 'text-red-400 bg-red-900/30 border-red-700/50';
    if (r === 'HOLD') return 'text-blue-400 bg-blue-900/30 border-blue-700/50';
    return 'text-yellow-400 bg-yellow-900/30 border-yellow-700/50';
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0">
          <Sparkles className="text-white" size={20} />
        </div>
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-gray-100">AI Strategy Lab</h2>
          <p className="text-sm font-mono text-gray-500 mt-1">Simulate trade entries and scenarios using live market context.</p>
        </div>
      </div>

      {/* Query Form */}
      <form onSubmit={handleSubmit} className="bg-[#121212] border border-gray-800 rounded-md p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-1">
            <label className="block text-xs font-mono text-gray-500 uppercase mb-2">Target Stock</label>
            <input 
              type="text" 
              value={ticker} 
              onChange={e => setTicker(e.target.value)}
              placeholder="e.g. RELIANCE" 
              disabled={loading}
              className="w-full bg-[#1a1a1a] border border-gray-700 rounded-md px-4 py-3 text-gray-100 font-mono text-sm uppercase placeholder-gray-600 focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>
          <div className="md:col-span-3">
            <label className="block text-xs font-mono text-gray-500 uppercase mb-2">Strategy Query / Scenario</label>
            <div className="flex gap-3">
              <input 
                type="text" 
                value={query} 
                onChange={e => setQuery(e.target.value)}
                placeholder="e.g. Should I buy now given recent negative news?" 
                disabled={loading}
                className="flex-1 bg-[#1a1a1a] border border-gray-700 rounded-md px-4 py-3 text-gray-100 font-sans text-sm placeholder-gray-600 focus:outline-none focus:border-purple-500 transition-colors"
              />
              <button 
                type="submit" 
                disabled={!ticker.trim() || !query.trim() || loading}
                className="px-6 auto py-3 bg-purple-600 hover:bg-purple-500 focus:ring-2 focus:ring-purple-400 rounded-md text-sm font-semibold text-white transition-all disabled:opacity-50 flex items-center gap-2 shrink-0"
              >
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                Simulate
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-950/50 border border-red-800 rounded-md flex items-start gap-3">
          <AlertTriangle className="text-red-400 shrink-0 mt-0.5" size={18} />
          <div>
            <p className="text-red-300 text-sm font-semibold">Simulation Failed</p>
            <p className="text-red-400/80 text-xs font-mono mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="py-12 flex flex-col items-center justify-center space-y-4">
          <div className="relative">
            <div className="w-12 h-12 border-4 border-gray-800 border-t-purple-500 rounded-full animate-spin"></div>
          </div>
          <p className="text-sm font-mono text-purple-400 animate-pulse uppercase tracking-widest">Compiling live market context...</p>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="bg-[#121212] border border-gray-800 rounded-xl overflow-hidden shadow-2xl animate-in slide-in-from-bottom-4 duration-500">
          <div className="p-6 border-b border-gray-800 flex justify-between items-center bg-[#161616]">
            <div>
              <p className="text-xs font-mono text-gray-500 uppercase tracking-widest mb-1">AI Recommendation</p>
              <h3 className="text-2xl font-bold font-mono text-gray-100">{ticker.toUpperCase()}</h3>
            </div>
            <div className={clsx("px-4 py-1.5 rounded-full border text-sm font-bold tracking-widest uppercase", getRecColor(result.recommendation))}>
              {result.recommendation}
            </div>
          </div>

          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-[#1a1a1a] p-4 rounded-lg border border-gray-800 flex items-start gap-4">
              <ArrowRight className="text-blue-400 shrink-0" />
              <div>
                <p className="text-xs font-mono text-gray-500 uppercase mb-1">Entry Range</p>
                <p className="text-gray-200 font-mono font-bold text-sm">{result.entry_range}</p>
              </div>
            </div>
            
            <div className="bg-[#1a1a1a] p-4 rounded-lg border border-gray-800 flex items-start gap-4">
              <ShieldCheck className="text-red-400 shrink-0" />
              <div>
                <p className="text-xs font-mono text-gray-500 uppercase mb-1">Stop Loss</p>
                <p className="text-red-300 font-mono font-bold text-sm">{result.stop_loss}</p>
              </div>
            </div>

            <div className="bg-[#1a1a1a] p-4 rounded-lg border border-gray-800 flex items-start gap-4">
              <Target className="text-green-400 shrink-0" />
              <div>
                <p className="text-xs font-mono text-gray-500 uppercase mb-1">Target Price</p>
                <p className="text-green-300 font-mono font-bold text-sm">{result.target_price}</p>
              </div>
            </div>
          </div>

          <div className="px-6 pb-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="flex items-center gap-2 text-sm font-mono text-gray-400 uppercase mb-3 border-b border-gray-800 pb-2">
                <Info size={16} className="text-purple-400" />
                Strategic Reasoning
              </h4>
              <p className="text-gray-300 text-sm leading-relaxed">{result.reasoning}</p>
              <div className="mt-4 flex items-center gap-2">
                <span className="text-xs font-mono text-gray-500">AI Confidence:</span>
                <span className={clsx("text-xs font-mono px-2 py-0.5 rounded border", 
                  result.confidence?.toUpperCase() === 'HIGH' ? 'bg-green-900/40 text-green-400 border-green-800' :
                  result.confidence?.toUpperCase() === 'LOW' ? 'bg-red-900/40 text-red-400 border-red-800' :
                  'bg-yellow-900/40 text-yellow-400 border-yellow-800'
                )}>
                  {result.confidence?.toUpperCase()}
                </span>
              </div>
            </div>
            
            <div>
              <h4 className="flex items-center gap-2 text-sm font-mono text-gray-400 uppercase mb-3 border-b border-gray-800 pb-2">
                <AlertTriangle size={16} className="text-orange-400" />
                Key Risks
              </h4>
              <ul className="space-y-2">
                {(result.risks || []).map((risk, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-300">
                    <span className="text-orange-500 mt-0.5">•</span>
                    <span className="leading-snug">{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          
          <div className="bg-red-950/20 border-t border-red-900/30 p-4 text-center">
            <p className="text-xs font-mono text-red-500 uppercase tracking-widest">
              ⚠️ This is AI-generated analysis for educational purposes only. Not financial advice.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
