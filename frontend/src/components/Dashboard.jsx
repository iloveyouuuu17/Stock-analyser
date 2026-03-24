import React from 'react';
import { PieChart, Pie, Cell, LineChart, Line, ComposedChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowUpRight, ArrowDownRight, Minus, AlertCircle, TrendingUp, TrendingDown, Activity, Clock, AlertTriangle, Zap, Shield, Star } from 'lucide-react';
import clsx from 'clsx';

const COLORS = {
  positive: '#22c55e',
  negative: '#ef4444',
  neutral:  '#6b7280',
  background: '#121212',
  border: '#27272a'
};

const EVENT_BADGE_STYLE = {
  'Earnings':        { bg: '#1e3a5f', color: '#60a5fa', emoji: '🏦' },
  'Corporate Action':{ bg: '#3b1f5e', color: '#c084fc', emoji: '📋' },
  'Board Meeting':   { bg: '#1f3b27', color: '#4ade80', emoji: '🗓️' },
  'Dividend':        { bg: '#1f3b1f', color: '#86efac', emoji: '💰' },
};

export default function Dashboard({ data, error, onAddToWatchlist }) {
  if (error) {
    return (
      <div className="w-full max-w-4xl mx-auto p-6 bg-[#161212] border border-red-900/50 rounded-md flex items-start gap-4">
        <AlertCircle className="text-red-500 mt-1" size={24} />
        <div>
          <h3 className="text-lg font-semibold text-red-500 mb-1">Error Analyzing Stock</h3>
          <p className="text-gray-300 font-mono text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const {
    stockInfo, news, sentimentSummary, fetched_at,
    sentimentPriceCorrelation, smartMoneyDivergences,
    aiSummary, sentimentMomentum, newsVelocity,
    insiderSignals, fiiDii
  } = data;

  const isPositiveChange = stockInfo.dailyChange >= 0;
  const ChangeIcon = isPositiveChange ? ArrowUpRight : ArrowDownRight;

  // Data freshness
  const dataAgeMs     = fetched_at ? Date.now() - new Date(fetched_at).getTime() : 0;
  const isStale       = dataAgeMs > 60 * 60 * 1000;
  const formattedTime = fetched_at
    ? new Date(fetched_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    : null;

  // Pie
  const pieData = [
    { name: 'Positive', value: sentimentSummary.positive, color: COLORS.positive },
    { name: 'Negative', value: sentimentSummary.negative, color: COLORS.negative },
    { name: 'Neutral',  value: sentimentSummary.neutral,  color: COLORS.neutral  },
  ].filter(d => d.value > 0);

  // Line chart — show dates on X axis
  const lineData = [...news].reverse().map(item => {
    let dateLabel = `#${item.chart_index}`;
    if (item.published) {
      try {
        const d = new Date(item.published);
        if (!isNaN(d)) dateLabel = d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
      } catch (_) {}
    }
    return { name: dateLabel, score: item.sentiment_score, title: item.title.substring(0, 30) + '...', fullTitle: item.title, label: item.sentiment_label };
  });

  const verdictColor =
    sentimentSummary.overall === 'Bullish' ? 'text-green-500' :
    sentimentSummary.overall === 'Bearish' ? 'text-red-500' : 'text-gray-400';

  // Momentum badge
  const momentumColor =
    sentimentMomentum?.direction === 'improving' ? 'text-green-400 bg-green-900/30 border-green-700/40' :
    sentimentMomentum?.direction === 'deteriorating' ? 'text-red-400 bg-red-900/30 border-red-700/40' :
    'text-gray-400 bg-gray-800/30 border-gray-700/40';

  // Format helpers
  // Indian convention: Lakh Crore (1e12) → Crore (1e7) → raw
  const formatMktCap = (n) => { if (!n) return 'N/A'; if (n >= 1e12) return `₹${(n/1e12).toFixed(2)} L Cr`; if (n >= 1e7) return `₹${(n/1e7).toFixed(2)} Cr`; return `₹${n.toLocaleString('en-IN')}`; };
  const formatVolume = (v) => { if (!v) return 'N/A'; if (v >= 1e7) return `${(v/1e7).toFixed(2)}Cr`; if (v >= 1e5) return `${(v/1e5).toFixed(2)}L`; return v.toLocaleString('en-IN'); };

  // History chart
  const combinedChartData = [
    ...(stockInfo.history || []).map(d => ({ date: d.date, History: d.price, Projection: null, range: null })),
    ...(stockInfo.projection || []).map(d => ({ date: d.date, History: null, Projection: d.projectedPrice, range: [d.projectedLower, d.projectedUpper].every(x => x != null) ? [d.projectedLower, d.projectedUpper] : null })),
  ];
  const historyIsUp  = stockInfo.projectedChange >= 0;
  const historyColor = historyIsUp ? COLORS.positive : COLORS.negative;

  // Beta context
  const betaContext = stockInfo.beta
    ? stockInfo.beta > 1.5 ? { text: `High Volatility — moves ${stockInfo.beta}x the market`, color: 'text-red-400', bg: 'border-red-900/40' }
    : stockInfo.beta >= 0.8 ? { text: 'Moderate Volatility — moves in line with market', color: 'text-yellow-400', bg: 'border-yellow-900/40' }
    : { text: 'Low Volatility — defensive stock', color: 'text-green-400', bg: 'border-green-900/40' }
    : null;

  // FII/DII format
  const formatCrores = (v) => {
    if (!v) return '₹0';
    const num = typeof v === 'string' ? parseFloat(v.replace(/,/g, '')) : v;
    if (isNaN(num)) return '₹0';
    return `₹${(num / 100).toFixed(0)}Cr`;
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 animate-in fade-in duration-500">

      {/* Feature 7: Circuit Breaker Banner */}
      {stockInfo.circuitBreaker && (
        <div className="w-full p-4 bg-red-950 border-2 border-red-600 rounded-md flex items-center gap-3 animate-pulse">
          <AlertTriangle size={24} className="text-red-400 shrink-0" />
          <div>
            <p className="text-red-300 font-bold text-sm">{stockInfo.circuitBreaker.message}</p>
            <p className="text-red-400/70 text-xs font-mono mt-0.5">
              {stockInfo.circuitBreaker.type === 'upper' ? 'Upper' : 'Lower'} circuit at ₹{stockInfo.circuitBreaker.circuit} · Current price at {stockInfo.circuitBreaker.proximity}%
            </p>
          </div>
        </div>
      )}

      {/* Feature 1: Gemini AI Summary */}
      {aiSummary && (
        <div className="relative overflow-hidden rounded-md p-[1px] bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600">
          <div className="bg-[#0d0d0d] rounded-md p-5">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">AI</div>
              <span className="text-xs font-mono text-purple-400 uppercase tracking-wider">Gemini Analyst Summary</span>
            </div>
            <p className="text-gray-200 text-sm leading-relaxed">{aiSummary}</p>
          </div>
        </div>
      )}

      {/* News Velocity Surge Warning */}
      {newsVelocity?.surge && (
        <div className="p-3 bg-amber-950/50 border border-amber-700/50 rounded-md flex items-center gap-3">
          <Zap size={18} className="text-amber-400 shrink-0" />
          <div>
            <span className="text-amber-300 font-semibold text-sm">⚡ News Surge — High Volatility Expected</span>
            <span className="text-amber-500/70 text-xs font-mono ml-3">
              {newsVelocity.count24h} headlines in 24h vs {newsVelocity.avgDaily} daily avg
            </span>
          </div>
        </div>
      )}

      {/* Data Freshness Bar */}
      {formattedTime && (
        <div className="flex items-center gap-2 text-xs font-mono text-gray-500">
          <Clock size={12} />
          Data as of {formattedTime}
          {isStale && (
            <span className="ml-2 px-2 py-0.5 bg-yellow-900/40 border border-yellow-700/50 text-yellow-400 rounded text-[10px] font-semibold">⚠ Stale Data</span>
          )}
        </div>
      )}

      {/* Header Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Price Card */}
        <div className="bg-[#121212] border border-gray-800 rounded-md p-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full" style={{ backgroundColor: isPositiveChange ? COLORS.positive : COLORS.negative }} />
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-mono text-gray-500">{stockInfo.ns_ticker}</p>
                {onAddToWatchlist && (
                  <button onClick={() => onAddToWatchlist(data.ticker)} className="text-gray-600 hover:text-yellow-400 transition-colors" title="Add to Watchlist">
                    <Star size={14} />
                  </button>
                )}
              </div>
              <h2 className="text-2xl font-bold tracking-tight text-gray-100">{stockInfo.shortName}</h2>
            </div>
            <div className="text-right">
              <div className="text-3xl font-mono font-bold text-gray-100">₹{stockInfo.currentPrice?.toFixed(2) || '---'}</div>
              <div className={clsx("flex items-center justify-end font-mono text-sm mt-1", isPositiveChange ? "text-green-500" : "text-red-500")}>
                <ChangeIcon size={16} className="mr-1" />
                {Math.abs(stockInfo.dailyChange).toFixed(2)} ({Math.abs(stockInfo.dailyChangePercent).toFixed(2)}%)
              </div>
            </div>
          </div>
        </div>

        {/* Verdict Card + Momentum Badge */}
        <div className="bg-[#121212] border border-gray-800 rounded-md p-6">
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm font-mono text-gray-500 uppercase tracking-wider">Overall Sentiment</p>
            {sentimentMomentum && (
              <span className={clsx('text-[10px] font-mono px-2 py-0.5 rounded border', momentumColor)}>
                {sentimentMomentum.label}
              </span>
            )}
          </div>
          <div className="flex items-end gap-4 mt-2">
            <h2 className={clsx("text-4xl font-bold tracking-tight uppercase", verdictColor)}>
              {sentimentSummary.overall}
            </h2>
            <div className="flex gap-3 mb-1 font-mono text-sm">
              <span className="text-green-500">+{sentimentSummary.positive}</span>
              <span className="text-gray-500">{sentimentSummary.neutral}</span>
              <span className="text-red-500">-{sentimentSummary.negative}</span>
            </div>
          </div>
          {sentimentSummary.weighted_score !== undefined && (
            <p className="text-xs font-mono text-gray-600 mt-2">
              Confidence-weighted score: {sentimentSummary.weighted_score > 0 ? '+' : ''}{(sentimentSummary.weighted_score * 100).toFixed(1)}
            </p>
          )}
        </div>
      </div>

      {/* Feature 4: Insider Signals */}
      {insiderSignals && insiderSignals.length > 0 && (
        <div className="space-y-2">
          {insiderSignals.map((sig, i) => (
            <div key={i} className={clsx("p-4 rounded-md border flex items-start gap-3",
              sig.type === 'accumulation' ? 'bg-emerald-950/30 border-emerald-700/40' : 'bg-orange-950/30 border-orange-700/40'
            )}>
              <span className="text-xl">{sig.emoji}</span>
              <div>
                <p className={clsx("text-sm font-semibold", sig.type === 'accumulation' ? 'text-emerald-300' : 'text-orange-300')}>
                  {sig.message}
                </p>
                <p className="text-xs font-mono text-gray-500 mt-0.5">{sig.detail}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Correlation + Divergences + Beta + FII/DII row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {sentimentPriceCorrelation !== null && sentimentPriceCorrelation !== undefined && (
          <div className="bg-[#121212] border border-gray-800 rounded-md p-5 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-blue-900/30 border border-blue-700/40 flex items-center justify-center shrink-0">
              <Activity size={22} className="text-blue-400" />
            </div>
            <div>
              <p className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-0.5">Sentiment–Price Correlation</p>
              <p className="text-gray-100 text-sm">
                Sentiment predicted price movement with <span className="text-blue-400 font-bold font-mono">{sentimentPriceCorrelation}%</span> accuracy.
              </p>
            </div>
          </div>
        )}

        {/* Feature 5: Beta */}
        {betaContext && (
          <div className={clsx("bg-[#121212] border rounded-md p-5 flex items-center gap-4", betaContext.bg)}>
            <div className="w-12 h-12 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center shrink-0">
              <Shield size={22} className={betaContext.color} />
            </div>
            <div>
              <p className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-0.5">Beta: <span className="text-gray-300">{stockInfo.beta}</span></p>
              <p className={clsx("text-sm", betaContext.color)}>{betaContext.text}</p>
            </div>
          </div>
        )}

        {/* Smart Money Divergences */}
        {smartMoneyDivergences && smartMoneyDivergences.length > 0 && (
          <div className="bg-[#121212] border border-yellow-900/40 rounded-md p-5 space-y-3">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle size={16} className="text-yellow-400" />
              <p className="text-xs font-mono text-yellow-400 uppercase tracking-wider">Smart Money Divergence</p>
            </div>
            {smartMoneyDivergences.map((evt, i) => (
              <div key={i} className="text-xs font-mono flex justify-between items-center border-b border-gray-800/50 pb-2 last:border-0 last:pb-0">
                <div>
                  <span className="text-gray-300">{evt.date}</span>
                  <span className="text-yellow-500 ml-3">{evt.type}</span>
                </div>
                <span className={clsx('font-bold', evt.priceMove >= 0 ? 'text-green-400' : 'text-red-400')}>
                  {evt.priceMove >= 0 ? '+' : ''}{evt.priceMove}%
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Feature 6: FII/DII */}
        {fiiDii && fiiDii.fii && (
          <div className="bg-[#121212] border border-gray-800 rounded-md p-5">
            <p className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">FII / DII Activity</p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] font-mono text-gray-600">FII Net</p>
                <p className={clsx("text-sm font-bold font-mono", fiiDii.fiiFlow === 'IN' ? 'text-green-400' : 'text-red-400')}>
                  {formatCrores(fiiDii.fii.netValue)}
                </p>
              </div>
              <div>
                <p className="text-[10px] font-mono text-gray-600">DII Net</p>
                <p className="text-sm font-bold font-mono text-blue-400">
                  {formatCrores(fiiDii.dii?.netValue)}
                </p>
              </div>
            </div>
            <div className={clsx("mt-2 text-[10px] font-mono px-2 py-1 rounded w-fit",
              fiiDii.fiiFlow === 'IN' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400')}>
              Foreign Money Flowing {fiiDii.fiiFlow} {fiiDii.fiiFlow === 'IN' ? '🟢' : '🔴'}
            </div>
          </div>
        )}
      </div>

      {/* Main Grid: Charts & News */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Analytics Column */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-[#121212] border border-gray-800 rounded-md p-4 flex flex-col items-center">
            <h3 className="text-sm font-mono text-gray-500 uppercase w-full mb-2">Sentiment Distribution</h3>
            <div className="w-full h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={2} dataKey="value" stroke="none">
                    {pieData.map((entry, index) => (<Cell key={`cell-${index}`} fill={entry.color} />))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', borderColor: '#333', color: '#fff' }} itemStyle={{ color: '#fff' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-[#121212] border border-gray-800 rounded-md p-4">
            <h3 className="text-sm font-mono text-gray-500 uppercase mb-4">Sentiment Over Time</h3>
            <div className="w-full h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineData} margin={{ top: 5, right: 10, left: -20, bottom: 20 }}>
                  <XAxis dataKey="name" stroke="#4b5563" fontSize={9} interval="preserveStartEnd" tick={{ fill: '#6b7280' }} />
                  <YAxis domain={[-1.1, 1.1]} ticks={[-1, 0, 1]} stroke="#4b5563" fontSize={10} tickFormatter={(t) => t > 0 ? '+1' : t} />
                  <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', borderColor: '#333', fontSize: '12px' }} labelFormatter={() => ''} formatter={(v, n, p) => [p.payload.label, p.payload.title]} />
                  <Line type="monotone" dataKey="score" stroke="#60a5fa" strokeWidth={2} dot={{ r: 3, fill: '#1e1e1e', strokeWidth: 2 }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="lg:col-span-2 space-y-6 flex flex-col">
          {(stockInfo.history?.length > 0) && (
            <div className="bg-[#121212] border border-gray-800 rounded-md p-6 relative">
              <div className="flex justify-between items-baseline mb-6">
                <h3 className="text-sm font-mono text-gray-300 uppercase tracking-wider">6 Month Price History</h3>
                <div className={clsx("text-xs font-mono px-2 py-1 rounded bg-[#1a1a1a] border", historyIsUp ? "border-green-500/30 text-green-400" : "border-red-500/30 text-red-400")}>
                  AI FORECAST: {historyIsUp ? '+' : ''}{stockInfo.projectedChangePercent?.toFixed(1)}% IN 6M
                </div>
              </div>
              <div className="w-full h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={combinedChartData} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                    <XAxis dataKey="date" stroke="#4b5563" fontSize={10} tickFormatter={(d) => { const dt = new Date(d); return `${dt.toLocaleString('default', {month:'short'})} '${dt.getFullYear().toString().substring(2)}`; }} minTickGap={30} />
                    <YAxis domain={['auto', 'auto']} stroke="#4b5563" fontSize={10} tickFormatter={(v) => `₹${v}`} />
                    <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', borderColor: '#333', color: '#fff', fontSize: '12px' }} itemStyle={{ color: '#fff' }} />
                    <Area type="monotone" dataKey="range" stroke="none" fill={historyColor} fillOpacity={0.15} activeDot={false} />
                    <Line type="monotone" dataKey="History" stroke={historyColor} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                    <Line type="monotone" dataKey="Projection" stroke={historyColor} strokeWidth={2} strokeDasharray="4 4" dot={false} activeDot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <p className="text-[10px] text-gray-600 font-mono mt-4 text-center italic">
                Projection based on historical patterns only — not financial advice.
              </p>
            </div>
          )}

          {/* Extended Stock Info */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-[#161212] border border-gray-800 rounded-md p-4">
              <div className="text-xs font-mono text-gray-500 uppercase mb-1">Market Cap</div>
              <div className="text-base font-bold text-gray-200">{formatMktCap(stockInfo.marketCap)}</div>
            </div>
            <div className="bg-[#161212] border border-gray-800 rounded-md p-4">
              <div className="text-xs font-mono text-gray-500 uppercase mb-1">P/E Ratio</div>
              <div className="text-base font-bold text-gray-200">{stockInfo.peRatio?.toFixed(2) || 'N/A'}</div>
            </div>
            <div className="bg-[#161212] border border-gray-800 rounded-md p-4">
              <div className="text-xs font-mono text-gray-500 uppercase mb-1">52W Range</div>
              <div className="text-xs font-mono text-gray-300">
                <span className="text-red-400">₹{stockInfo.fiftyTwoWeekLow?.toFixed(2) || '-'}</span>
                <span className="text-gray-600 mx-1">/</span>
                <span className="text-green-400">₹{stockInfo.fiftyTwoWeekHigh?.toFixed(2) || '-'}</span>
              </div>
            </div>
            <div className="bg-[#161212] border border-gray-800 rounded-md p-4">
              <div className="text-xs font-mono text-gray-500 uppercase mb-1">Volume</div>
              <div className="text-sm font-bold text-gray-200">{formatVolume(stockInfo.volume)}</div>
              <div className="text-[10px] font-mono text-gray-500 mt-1">Avg: {formatVolume(stockInfo.averageVolume)}</div>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-[#161212] border border-gray-800 rounded-md p-4 flex justify-between">
              <span className="text-xs font-mono text-gray-500 uppercase">Sector</span>
              <span className="text-sm font-semibold text-gray-300">{stockInfo.sector}</span>
            </div>
            <div className="bg-[#161212] border border-gray-800 rounded-md p-4 flex justify-between">
              <span className="text-xs font-mono text-gray-500 uppercase">Industry</span>
              <span className="text-sm font-semibold text-gray-300 text-right">{stockInfo.industry}</span>
            </div>
          </div>

          {/* News Terminal */}
          <div className="bg-[#121212] border border-gray-800 rounded-md overflow-hidden flex flex-col flex-grow">
            <div className="bg-[#1a1a1a] p-3 border-b border-gray-800 flex justify-between items-center">
              <h3 className="text-sm font-mono text-gray-300 uppercase tracking-wider">News Terminal Log</h3>
              <span className="text-xs text-gray-500 font-mono">Found {news.length} articles</span>
            </div>
            <div className="overflow-y-auto max-h-[600px] p-0 custom-scrollbar">
              {news.map((item, idx) => {
                const rowColor =
                  item.sentiment_label === 'Positive' ? 'text-green-400 border-green-500' :
                  item.sentiment_label === 'Negative' ? 'text-red-400 border-red-500' : 'text-gray-400 border-gray-600';
                const badgeStyle = item.event_badge ? EVENT_BADGE_STYLE[item.event_badge] : null;

                return (
                  <div key={idx} className="flex border-b border-gray-800/50 hover:bg-[#1a1a1a] transition-colors p-4 group">
                    <div className="w-16 shrink-0 pt-0.5">
                      <div className={clsx("text-[10px] font-mono border px-1.5 py-0.5 rounded flex items-center justify-center w-fit", rowColor)}>
                        {item.sentiment_label.toUpperCase()}
                      </div>
                    </div>
                    <div className="flex-1 ml-4 pr-4">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        {badgeStyle && (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                                style={{ backgroundColor: badgeStyle.bg, color: badgeStyle.color }}>
                            {badgeStyle.emoji} {item.event_badge}
                          </span>
                        )}
                      </div>
                      <a href={item.link} target="_blank" rel="noopener noreferrer"
                         className="text-sm text-gray-200 group-hover:text-blue-400 transition-colors font-medium leading-relaxed block mb-1">
                        {item.title}
                      </a>
                      <div className="flex items-center gap-3 text-xs font-mono text-gray-600">
                        <span>{item.source}</span>
                        {item.published && <span>• {new Date(item.published).toLocaleDateString()}</span>}
                        {item.confidence && <span>• {(item.confidence * 100).toFixed(0)}% conf</span>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
