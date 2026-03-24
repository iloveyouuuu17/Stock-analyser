import React, { useState } from 'react';
import axios from 'axios';
import Search from './components/Search';
import Dashboard from './components/Dashboard';
import LoadingSkeleton from './components/LoadingSkeleton';
import Heatmap from './components/Heatmap';
import Portfolio from './components/Portfolio';
import Watchlist, { addToWatchlist } from './components/Watchlist';
import StrategyLab from './components/StrategyLab';
import GlobalPulse from './components/GlobalPulse';

const TABS = [
  { id: 'analysis',  label: 'Stock Analysis' },
  { id: 'heatmap',   label: 'Market Heatmap' },
  { id: 'portfolio', label: 'Portfolio' },
  { id: 'watchlist', label: '★ Watchlist' },
  { id: 'strategy',  label: 'Strategy Lab' },
];

function App() {
  const [activeTab, setActiveTab] = useState('analysis');
  const [data,      setData]      = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error,     setError]     = useState(null);

  const handleSearch = async (ticker) => {
    setIsLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await axios.get(`http://localhost:8000/api/stock/${ticker}`);
      setData(response.data);
    } catch (err) {
      if (err.response) {
        setError(err.response.data.detail || `Server Error: ${err.response.status}`);
      } else if (err.request) {
        setError('Backend Unreachable: Please ensure the API is running on localhost:8000');
      } else {
        setError(`Error: ${err.message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddToWatchlist = (ticker) => {
    addToWatchlist(ticker);
    // Brief visual feedback
    alert(`${ticker} added to Watchlist ★`);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-gray-100 font-sans selection:bg-gray-800">
      {/* Header */}
      <header className="border-b border-gray-900 bg-[#0f0f0f]">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-blue-500">
            <span className="text-xl font-bold tracking-tighter">
              <span className="text-green-500">{'>'}</span>_ IS<span className="text-gray-400">SA</span>
            </span>
          </div>
          <div className="text-xs font-mono text-gray-500 uppercase tracking-widest">
            Indian Stock Sentiment Analyzer
          </div>
        </div>

        {/* Tabs */}
        <div className="max-w-6xl mx-auto px-4 flex gap-1 pb-0">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-xs font-mono uppercase tracking-widest border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-10">
        {activeTab === 'analysis' && (
          <>
            <Search onSearch={handleSearch} isLoading={isLoading} />
            {isLoading && <LoadingSkeleton />}
            {!isLoading && <Dashboard data={data} error={error} onAddToWatchlist={handleAddToWatchlist} />}
            {!isLoading && !data && !error && (
              <div className="text-center mt-20 fade-in duration-700">
                <h2 className="text-2xl font-bold tracking-tight text-gray-400 mb-2">Awaiting Target Selection</h2>
                <p className="text-gray-600 font-mono text-sm max-w-lg mx-auto leading-relaxed">
                  Enter an NSE ticker above or select a trending stock to initiate live market sentiment analysis powered by FinBERT Natural Language Processing.
                </p>
              </div>
            )}
            <div className="mt-8">
              <GlobalPulse />
            </div>
          </>
        )}
        {activeTab === 'heatmap' && <Heatmap onNavigateToAnalysis={(ticker) => {
          setActiveTab('analysis');
          handleSearch(ticker);
        }} />}
        {activeTab === 'portfolio' && <Portfolio />}
        {activeTab === 'watchlist' && <Watchlist />}
        {activeTab === 'strategy' && <StrategyLab />}
      </main>
    </div>
  );
}

export default App;
