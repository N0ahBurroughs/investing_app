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
const DEFAULT_SYMBOLS = ["AAPL", "MSFT", "NVDA", "AMZN", "TSLA"];

const sampleStrategy = `Name: Momentum Daily\nUniverse: AAPL, MSFT, NVDA\nMax_Position_Pct: 0.1\nMax_Risk_Score: 0.6\nEntry: Buy when price above 20-day SMA and RSI < 70\nExit: Sell when price below 20-day SMA or RSI > 75`;
const strategyPresets = {
  safe: `Name: Defensive Core\nUniverse: AAPL, MSFT, JNJ, PG\nMax_Position_Pct: 0.08\nMax_Risk_Score: 0.4\nEntry: Buy when price above 20-day SMA and RSI < 65\nExit: Sell when price below 20-day SMA or RSI > 70`,
  balanced: `Name: Balanced Trend\nUniverse: AAPL, MSFT, NVDA, AMZN\nMax_Position_Pct: 0.12\nMax_Risk_Score: 0.6\nEntry: Buy when price above 20-day SMA and RSI between 45 and 70\nExit: Sell when price below 20-day SMA or RSI > 75`,
  risky: `Name: Aggressive Momentum\nUniverse: NVDA, TSLA, AMD, COIN\nMax_Position_Pct: 0.2\nMax_Risk_Score: 0.8\nEntry: Buy when price above 20-day SMA and RSI < 75\nExit: Sell when price below 20-day SMA or RSI > 80`
};

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
  const [userId, setUserId] = useState(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authMode, setAuthMode] = useState("login");
  const [authError, setAuthError] = useState("");
  const [setupComplete, setSetupComplete] = useState(false);
  const [setupError, setSetupError] = useState("");
  const [setupConflicts, setSetupConflicts] = useState([]);
  const [initialCapital, setInitialCapital] = useState(100000);
  const [provider, setProvider] = useState("finnhub");
  const [historyRange, setHistoryRange] = useState("1M");
  const [portfolio, setPortfolio] = useState(null);
  const [trades, setTrades] = useState([]);
  const [market, setMarket] = useState(null);
  const [marketHistory, setMarketHistory] = useState({});
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
    const symbolList = DEFAULT_SYMBOLS.join(",");
    const res = await fetch(`${API_BASE}/market?symbols=${symbolList}&provider=${provider}`);
    if (res.ok) {
      const data = await res.json();
      setMarket(data);
    }
  };

  const getRangeDays = () => {
    if (historyRange === "1D") return 1;
    if (historyRange === "5D") return 5;
    if (historyRange === "1M") return 30;
    if (historyRange === "1Y") return 365;
    if (historyRange === "YTD") {
      const now = new Date();
      const start = new Date(now.getFullYear(), 0, 1);
      const diff = Math.max(1, Math.ceil((now - start) / (1000 * 60 * 60 * 24)));
      return diff;
    }
    return 30;
  };

  const fetchHistory = async () => {
    const days = getRangeDays();
    const entries = await Promise.all(
      DEFAULT_SYMBOLS.map(async (symbol) => {
        const res = await fetch(`${API_BASE}/history?symbol=${symbol}&days=${days}&provider=${provider}`);
        if (res.ok) {
          const data = await res.json();
          return [symbol, data.history || []];
        }
        return [symbol, marketHistory[symbol] || []];
      })
    );
    setMarketHistory(Object.fromEntries(entries));
  };

  const fetchStrategies = async () => {
    const res = await fetch(`${API_BASE}/strategies?user_id=${userId}`);
    if (res.ok) {
      const data = await res.json();
      setStrategies(data);
    }
  };

  useEffect(() => {
    if (!userId) return;
    fetchPortfolio();
    fetchTrades();
    fetchMarket();
    fetchHistory();
    fetchStrategies();
    const timer = setInterval(() => {
      fetchPortfolio();
      fetchTrades();
      fetchMarket();
    }, 15000);
    return () => clearInterval(timer);
  }, [userId, provider, historyRange]);

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
      body: JSON.stringify({ user_id: userId, content: strategyText, provider })
    });
    if (res.ok) {
      const data = await res.json();
      setRefinements(data.refinements || []);
      fetchTrades();
      fetchPortfolio();
    }
  };

  const handleAuth = async () => {
    setAuthError("");
    if (!username || !password) {
      setAuthError("Username and password are required.");
      return;
    }
    const endpoint = authMode === "register" ? "/auth/register" : "/auth/login";
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: username.trim().toLowerCase(),
        password
      })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setAuthError(data.detail || "Authentication failed.");
      return;
    }
    setUserId(data.user_id);
    setSetupComplete(Boolean(data.setup_complete));
  };

  const handleSetup = async () => {
    setSetupError("");
    if (!strategyText.trim()) {
      setSetupError("Strategy is required.");
      return;
    }
    const res = await fetch(`${API_BASE}/user/setup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        initial_capital: Number(initialCapital),
        strategy: strategyText
      })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setSetupError(data.detail || "Setup failed.");
      return;
    }
    setSetupConflicts(data.conflicts || []);
    setSetupComplete(true);
    fetchPortfolio();
    fetchTrades();
    fetchMarket();
    fetchHistory();
    fetchStrategies();
  };

  const handleLogout = () => {
    setUserId(null);
    setUsername("");
    setPassword("");
    setPortfolio(null);
    setTrades([]);
    setMarket(null);
    setMarketHistory({});
    setStrategies([]);
    setConflicts([]);
    setRefinements([]);
    setSetupComplete(false);
    setAuthError("");
    setSetupError("");
    setSetupConflicts([]);
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

  if (!userId) {
    return (
      <div className="min-h-screen px-6 py-12 flex items-center justify-center">
        <div className="card p-8 w-full max-w-lg">
          <p className="text-sm uppercase tracking-[0.4em] text-slate-500 mb-3">AI Investing Platform</p>
          <h1 className="text-3xl font-display mb-4">{authMode === "register" ? "Create account" : "Sign in"}</h1>
          <div className="space-y-4">
            <input
              className="w-full px-3 py-2 rounded-lg border border-slate-300"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <input
              className="w-full px-3 py-2 rounded-lg border border-slate-300"
              placeholder="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {authError && <p className="text-sm text-ember">{authError}</p>}
            <button onClick={handleAuth} className="w-full px-4 py-2 rounded-lg bg-ink text-white">
              {authMode === "register" ? "Create Account" : "Sign In"}
            </button>
            <button
              onClick={() => setAuthMode(authMode === "register" ? "login" : "register")}
              className="w-full px-4 py-2 rounded-lg border border-slate-300"
            >
              {authMode === "register" ? "I already have an account" : "Create a new account"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!setupComplete) {
    return (
      <div className="min-h-screen px-6 py-12 flex items-center justify-center">
        <div className="card p-8 w-full max-w-2xl">
          <p className="text-sm uppercase tracking-[0.4em] text-slate-500 mb-3">Initial Setup</p>
          <h1 className="text-3xl font-display mb-4">Fund your account and set a strategy</h1>
          <div className="space-y-4">
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setStrategyText(strategyPresets.safe)}
                className="px-3 py-1 rounded-full text-xs border border-slate-300 text-slate-700"
              >
                Safe
              </button>
              <button
                onClick={() => setStrategyText(strategyPresets.balanced)}
                className="px-3 py-1 rounded-full text-xs border border-slate-300 text-slate-700"
              >
                Balanced
              </button>
              <button
                onClick={() => setStrategyText(strategyPresets.risky)}
                className="px-3 py-1 rounded-full text-xs border border-slate-300 text-slate-700"
              >
                Risky
              </button>
              <button
                onClick={() => setStrategyText(sampleStrategy)}
                className="px-3 py-1 rounded-full text-xs border border-slate-300 text-slate-700"
              >
                Custom
              </button>
            </div>
            <input
              className="w-full px-3 py-2 rounded-lg border border-slate-300"
              placeholder="Starting capital"
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
            />
            <textarea
              className="w-full h-48 p-3 rounded-lg border border-slate-300 text-sm"
              value={strategyText}
              onChange={(e) => setStrategyText(e.target.value)}
            />
            {setupError && <p className="text-sm text-ember">{setupError}</p>}
            {setupConflicts.length > 0 && (
              <p className="text-sm text-ember">Strategy conflicts: {setupConflicts.join("; ")}</p>
            )}
            <button onClick={handleSetup} className="w-full px-4 py-2 rounded-lg bg-ink text-white">
              Save & Continue
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-6 py-8">
      <header className="flex flex-col md:flex-row justify-between gap-4 mb-8">
        <div>
          <p className="text-sm uppercase tracking-[0.4em] text-slate-500">AI Investing Platform</p>
          <h1 className="text-3xl md:text-4xl font-display">Real-Time Strategy Command Center</h1>
        </div>
        <div className="flex gap-3 items-center">
          <span className="text-sm text-slate-600">{username || "Trader"}</span>
          <select
            className="px-3 py-2 rounded-lg border border-slate-300"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          >
            <option value="finnhub">Finnhub</option>
            <option value="mock">Mock</option>
            <option value="marketwatch">MarketWatch</option>
          </select>
          <button onClick={handleStart} className="px-4 py-2 rounded-lg bg-emerald-600 text-white">Start</button>
          <button onClick={handleRunOnce} className="px-4 py-2 rounded-lg bg-accent text-white">Run Once</button>
          <button onClick={handleStop} className="px-4 py-2 rounded-lg bg-slate-800 text-white">Stop</button>
          <button onClick={handleLogout} className="px-4 py-2 rounded-lg border border-slate-300">Logout</button>
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
          <div className="flex gap-2 mb-4 flex-wrap">
            {["1D", "5D", "1M", "YTD", "1Y"].map((range) => (
              <button
                key={range}
                onClick={() => setHistoryRange(range)}
                className={`px-3 py-1 rounded-full text-xs border ${historyRange === range ? "bg-ink text-white border-ink" : "border-slate-300 text-slate-700"}`}
              >
                {range}
              </button>
            ))}
          </div>
          <div className="space-y-4">
            {market?.indicators && Object.entries(market.indicators).map(([symbol, data]) => (
              <div key={symbol} className="border-b border-slate-200 pb-3">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-display">{symbol}</p>
                  <p>${Number(data.price).toFixed(2)}</p>
                </div>
                <div className="h-20">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={(marketHistory[symbol] || []).map((h) => ({ name: h.date, value: h.close }))}
                    >
                      <Line type="monotone" dataKey="value" stroke="#0ea5e9" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
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
