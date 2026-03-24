import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Globe, Search, AlertCircle, Loader2 } from 'lucide-react';
import clsx from 'clsx';

export default function GlobalPulse() {
  const [autoData, setAutoData] = useState(null);
  const [loadingAuto, setLoadingAuto] = useState(true);
  const [autoError, setAutoError] = useState(null);

  const [query, setQuery] = useState('');
  const [manualData, setManualData] = useState(null);
  const [loadingManual, setLoadingManual] = useState(false);
  const [manualError, setManualError] = useState(null);

  useEffect(() => {
    let mounted = true;
    axios.get('http://localhost:8000/api/global-pulse')
      .then(res => {
        if (mounted) setAutoData(res.data);
      })
      .catch(err => {
        if (mounted) setAutoError('Global Pulse AI analysis temporarily unavailable.');
      })
      .finally(() => {
        if (mounted) setLoadingAuto(false);
      });
    return () => { mounted = false; };
  }, []);

  const handleManualQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoadingManual(true);
    setManualError(null);
    setManualData(null);

    try {
      const res = await axios.post('http://localhost:8000/api/global-pulse/query', {
        scenario: query.trim()
      });
      setManualData(res.data);
    } catch (err) {
      setManualError(err.response?.data?.detail || 'Failed to analyze scenario.');
    } finally {
      setLoadingManual(false);
    }
  };

  const currentData = manualData || autoData;
  const sourceLabel = manualData ? 'What-If Scenario Analysis' : (autoData ? 'Automated Macro Tracker (BBC/Reuters)' : '');

  return (
    <div className="bg-[#121212] border border-gray-800 rounded-md p-6">
      <div className="flex items-center gap-2 mb-5">
        <Globe className="text-blue-500" size={20} />
        <h3 className="text-lg font-bold text-gray-100 uppercase tracking-wider">Global Pulse</h3>
        <span className="text-xs font-mono text-gray-500 ml-2 mt-1">Macro Events Impact Predictor</span>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Left Side: Input & Status */}
        <div className="lg:w-1/3 space-y-4">
          <form onSubmit={handleManualQuery} className="space-y-3">
            <label className="text-xs font-mono text-gray-400 uppercase">What-If Scenario Simulator</label>
            <div className="flex bg-[#1a1a1a] border border-gray-700 rounded-md overflow-hidden focus-within:border-blue-500 transition-colors">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. US imposes new H1B restrictions"
                className="flex-1 bg-transparent px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none"
                disabled={loadingManual}
              />
              <button
                type="submit"
                disabled={loadingManual || !query.trim()}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50 transition-colors flex items-center justify-center shrink-0"
              >
                {loadingManual ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
              </button>
            </div>
            {manualData && (
              <button 
                type="button" 
                onClick={() => { setManualData(null); setQuery(''); }}
                className="text-xs font-mono text-gray-500 hover:text-gray-300 underline"
              >
                Clear Scenario & Return to Live Feed
              </button>
            )}
          </form>

          {manualError && (
             <p className="text-xs text-red-400 font-mono mt-2">{manualError}</p>
          )}

          <div className="p-3 bg-blue-950/20 border border-blue-900/40 rounded flex items-start gap-2 mt-4">
             <AlertCircle size={14} className="text-blue-400 mt-0.5 shrink-0" />
             <p className="text-[10px] text-blue-300 font-mono leading-relaxed">
               Uses localized LLM analysis to predict down-stream sector impacts on Indian equities from live geopolitical events or manual what-if queries.
             </p>
          </div>
        </div>

        {/* Right Side: Table output */}
        <div className="lg:w-2/3">
          {loadingAuto && !manualData && !loadingManual ? (
            <div className="h-full min-h-[150px] flex items-center justify-center border border-gray-800 border-dashed rounded-md bg-[#161616]">
              <div className="flex items-center gap-3 text-gray-500 font-mono text-sm">
                <Loader2 size={16} className="animate-spin" />
                Scanning global headlines...
              </div>
            </div>
          ) : autoError && !manualData ? (
            <div className="h-full min-h-[150px] flex items-center justify-center border border-red-900/50 rounded-md bg-red-950/20 text-red-400 font-mono text-sm">
              {autoError}
            </div>
          ) : loadingManual ? (
            <div className="h-full min-h-[150px] flex flex-col items-center justify-center border border-blue-900/50 rounded-md bg-blue-950/10">
              <Loader2 size={24} className="animate-spin text-blue-500 mb-2" />
              <p className="text-blue-400 font-mono text-xs uppercase tracking-widest">Simulating Market Impact...</p>
            </div>
          ) : currentData && currentData.impacts ? (
            <div className="border border-gray-800 rounded-md overflow-hidden">
              <div className="bg-[#1a1a1a] px-4 py-2 border-b border-gray-800 flex justify-between items-center">
                <span className="text-[10px] font-mono text-gray-400 uppercase tracking-widest">Predicted Sector Impact</span>
                <span className="text-[9px] font-mono text-blue-500 px-2 py-0.5 rounded border border-blue-900/50 bg-blue-950/30">
                  {sourceLabel}
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm font-sans">
                  <thead className="text-[10px] uppercase font-mono text-gray-500 bg-[#121212]">
                    <tr>
                      <th className="px-4 py-3">Sector</th>
                      <th className="px-4 py-3">Impact</th>
                      <th className="px-4 py-3">Timeframe</th>
                      <th className="px-4 py-3">Confidence</th>
                      <th className="px-4 py-3">Reasoning</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/50 border-t border-gray-800">
                    {currentData.impacts.map((row, i) => (
                      <tr key={i} className="hover:bg-[#1a1a1a] transition-colors">
                        <td className="px-4 py-3 font-semibold text-gray-200">{row.sector}</td>
                        <td className="px-4 py-3">
                          <span className={clsx("text-xs font-mono font-bold", 
                            row.impact?.toUpperCase() === 'POSITIVE' ? 'text-green-400' :
                            row.impact?.toUpperCase() === 'NEGATIVE' ? 'text-red-400' : 'text-gray-400'
                          )}>
                            {row.impact}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-400">{row.timeframe}</td>
                        <td className="px-4 py-3">
                           <span className={clsx("text-[10px] font-mono px-1.5 py-0.5 rounded", 
                            row.confidence?.toUpperCase() === 'HIGH' ? 'bg-green-900/30 text-green-400' :
                            row.confidence?.toUpperCase() === 'LOW' ? 'bg-red-900/30 text-red-400' : 'bg-yellow-900/30 text-yellow-400'
                          )}>
                            {row.confidence}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-400 max-w-[200px] truncate" title={row.reason}>
                          {row.reason}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[150px] flex items-center justify-center border border-gray-800 border-dashed rounded-md bg-[#161616] text-gray-500 font-mono text-sm">
              No significant macro events detected.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
