import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const sampleStrategy = `Name: Momentum Daily\nUniverse: AAPL, MSFT, NVDA\nMax_Position_Pct: 0.1\nMax_Risk_Score: 0.6\nEntry: Buy when price above 20-day SMA and RSI < 70\nExit: Sell when price below 20-day SMA or RSI > 75`;

function StatCard({ label, value, accent }) {
  return (
    <div className="card p-5 flex flex-col gap-2">
      <span className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</span>
      <span className={`text-2xl font-display ${accent || "text-ink"}`}>{value}</span>
    </div>
  );
}

function Pill({ text }) {
  return <span className="px-3 py-1 rounded-full text-xs bg-slate-200 text-slate-700">{text}</span>;
}

export default function App() {
  const [userId, setUserId] = useState(1);
  const [portfolio, setPortfolio] = useState(null);
  const [trades, setTrades] = useState([]);
  const [market, setMarket] = useState(null);
  const [strategyText, setStrategyText] = useState(sampleStrategy);
  const [conflicts, setConflicts] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [equityCurve, setEquityCurve] = useState([]);
  const [refinements, setRefinements] = useState([]);

  const fetchPortfolio = async () => {
    const res = await fetch(`${API_BASE}/portfolio?user_id=${userId}`);
    if (res.ok) {
      const data = await res.json();
      setPortfolio(data);
    }
  };

  const fetchTrades = async () => {
    const res = await fetch(`${API_BASE}/trades?user_id=${userId}`);
    if (res.ok) {
      const data = await res.json();
      setTrades(data);
    }
  };

  const fetchMarket = async () => {
    const res = await fetch(`${API_BASE}/market?symbols=AAPL,MSFT,NVDA,AMZN,TSLA`);
    if (res.ok) {
      const data = await res.json();
      setMarket(data);
    }
  };

  const fetchStrategies = async () => {
    const res = await fetch(`${API_BASE}/strategies?user_id=${userId}`);
    if (res.ok) {
      const data = await res.json();
      setStrategies(data);
    }
  };

  useEffect(() => {
    fetchPortfolio();
    fetchTrades();
    fetchMarket();
    fetchStrategies();
    const timer = setInterval(() => {
      fetchPortfolio();
      fetchTrades();
      fetchMarket();
    }, 15000);
    return () => clearInterval(timer);
  }, [userId]);

  const handleStrategySave = async () => {
    const res = await fetch(`${API_BASE}/strategy`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, content: strategyText })
    });
    if (res.ok) {
      const data = await res.json();
      setConflicts(data.conflicts || []);
      fetchStrategies();
    }
  };

  const handleStart = async () => {
    await fetch(`${API_BASE}/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
  };

  const handleRunOnce = async () => {
    const res = await fetch(`${API_BASE}/trade/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, content: strategyText, provider: "marketwatch" })
    });
    if (res.ok) {
      const data = await res.json();
      setRefinements(data.refinements || []);
      fetchTrades();
      fetchPortfolio();
    }
  };

  const handleStop = async () => {
    await fetch(`${API_BASE}/stop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
  };

  const holdings = useMemo(() => {
    if (!portfolio) return [];
    return Object.values(portfolio.positions || {});
  }, [portfolio]);

  const heatmap = useMemo(() => {
    if (!portfolio || !market) return [];
    const total = holdings.reduce((sum, pos) => {
      const price = market.indicators?.[pos.symbol]?.price || 0;
      return sum + price * pos.quantity;
    }, portfolio.cash || 0);
    return holdings.map((pos) => {
      const price = market.indicators?.[pos.symbol]?.price || 0;
      const value = price * pos.quantity;
      const pct = total ? value / total : 0;
      return { symbol: pos.symbol, pct, value };
    });
  }, [portfolio, market, holdings]);

  return (
    <div className="min-h-screen px-6 py-8">
      <header className="flex flex-col md:flex-row justify-between gap-4 mb-8">
        <div>
          <p className="text-sm uppercase tracking-[0.4em] text-slate-500">AI Investing Platform</p>
          <h1 className="text-3xl md:text-4xl font-display">Real-Time Strategy Command Center</h1>
        </div>
        <div className="flex gap-3 items-center">
          <input
            className="px-3 py-2 rounded-lg border border-slate-300"
            type="number"
            value={userId}
            onChange={(e) => setUserId(Number(e.target.value))}
          />
          <button onClick={handleStart} className="px-4 py-2 rounded-lg bg-emerald-600 text-white">Start</button>
          <button onClick={handleRunOnce} className="px-4 py-2 rounded-lg bg-accent text-white">Run Once</button>
          <button onClick={handleStop} className="px-4 py-2 rounded-lg bg-slate-800 text-white">Stop</button>
        </div>
      </header>

      <section className="grid md:grid-cols-3 gap-4 mb-8">
        <StatCard label="Total Value" value={portfolio ? `$${(portfolio.cash + holdings.reduce((s, p) => s + p.quantity * (market?.indicators?.[p.symbol]?.price || 0), 0)).toFixed(2)}` : "--"} />
        <StatCard label="Cash" value={portfolio ? `$${portfolio.cash.toFixed(2)}` : "--"} accent="text-moss" />
        <StatCard label="Realized P&L" value={portfolio ? `$${portfolio.realized_pnl.toFixed(2)}` : "--"} accent="text-ember" />
      </section>

      <section className="grid lg:grid-cols-[2fr_1fr] gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-xl">Portfolio Growth</h2>
            <Pill text="Live" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equityCurve.length ? equityCurve : trades.map((t, i) => ({ name: i + 1, value: t.price }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#0ea5e9" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card p-6">
          <h2 className="font-display text-xl mb-4">Risk Exposure Heatmap</h2>
          <div className="grid grid-cols-2 gap-3">
            {heatmap.length === 0 && <p className="text-slate-500">No holdings yet.</p>}
            {heatmap.map((item) => (
              <div
                key={item.symbol}
                className="rounded-xl p-3 text-white"
                style={{ background: `rgba(14, 165, 233, ${Math.max(item.pct, 0.1)})` }}
              >
                <p className="text-sm uppercase">{item.symbol}</p>
                <p className="text-lg font-display">{(item.pct * 100).toFixed(1)}%</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-3 gap-6 mb-8">
        <div className="card p-6 lg:col-span-2">
          <h2 className="font-display text-xl mb-4">Live Trades Feed</h2>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {trades.length === 0 && <p className="text-slate-500">No trades yet.</p>}
            {trades.map((trade, idx) => (
              <div key={idx} className="flex items-center justify-between border-b border-slate-200 pb-2">
                <div>
                  <p className="font-display">{trade.symbol} · {trade.action}</p>
                  <p className="text-xs text-slate-500">{trade.reasoning}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm">Qty {trade.quantity}</p>
                  <p className="text-xs text-slate-500">{new Date(trade.created_at).toLocaleTimeString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-6">
          <h2 className="font-display text-xl mb-4">Market View</h2>
          <div className="space-y-2">
            {market?.indicators && Object.entries(market.indicators).map(([symbol, data]) => (
              <div key={symbol} className="flex items-center justify-between border-b border-slate-200 pb-2">
                <p className="font-display">{symbol}</p>
                <p>${Number(data.price).toFixed(2)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="font-display text-xl mb-4">Strategy Panel</h2>
          <textarea
            className="w-full h-48 p-3 rounded-lg border border-slate-300 text-sm"
            value={strategyText}
            onChange={(e) => setStrategyText(e.target.value)}
          />
          <div className="flex items-center gap-3 mt-4">
            <button onClick={handleStrategySave} className="px-4 py-2 rounded-lg bg-ink text-white">Save Strategy</button>
            {conflicts.length > 0 && <Pill text={`${conflicts.length} conflicts`}/>} 
          </div>
          {conflicts.length > 0 && (
            <ul className="mt-3 text-sm text-ember list-disc list-inside">
              {conflicts.map((c, idx) => <li key={idx}>{c}</li>)}
            </ul>
          )}
        </div>
        <div className="card p-6">
          <h2 className="font-display text-xl mb-4">Multi-Strategy Comparison</h2>
          <div className="space-y-3">
            {strategies.length === 0 && <p className="text-slate-500">No strategies saved.</p>}
            {strategies.map((s) => (
              <div key={s.id} className="flex items-center justify-between border-b border-slate-200 pb-2">
                <div>
                  <p className="font-display">{s.name}</p>
                  <p className="text-xs text-slate-500">{new Date(s.created_at).toLocaleDateString()}</p>
                </div>
                <Pill text={s.active ? "Active" : "Inactive"} />
              </div>
            ))}
          </div>
          {refinements.length > 0 && (
            <div className="mt-4">
              <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Refinement Suggestions</p>
              <ul className="mt-2 text-sm list-disc list-inside text-slate-700">
                {refinements.map((r, idx) => <li key={idx}>{r}</li>)}
              </ul>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
