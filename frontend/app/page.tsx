"use client";
import { useEffect, useState } from "react";
import { api, clearToken } from "@/lib/api";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"];

export default function Dashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.get("/analytics/summary");
        setSummary(data);
      } catch (e: any) {
        setError(e?.response?.data?.detail || e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-indigo-400 text-xl animate-pulse">Loading dashboard...</div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="bg-red-950 border border-red-700 rounded-xl p-6 max-w-lg text-center">
        <div className="text-red-400 text-lg font-semibold mb-2">⚠️ API Error</div>
        <div className="text-gray-300 text-sm font-mono">{error}</div>
      </div>
    </div>
  );

  const { totals, by_category = [], by_priority = [] } = summary;
  const resRate = totals.resolution_rate > 1
    ? totals.resolution_rate
    : Math.round(totals.resolution_rate * 100);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">🎫 Agentic Ticket System</h1>
          <p className="text-gray-400 mt-1">AI-powered IT support · {totals.total.toLocaleString()} tickets processed</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {[
            { label: "Total",      value: totals.total,     color: "text-white",      bg: "bg-gray-800" },
            { label: "Open",       value: totals.open,      color: "text-yellow-400", bg: "bg-yellow-950" },
            { label: "Resolved",   value: totals.resolved,  color: "text-green-400",  bg: "bg-green-950" },
            { label: "Critical",   value: totals.critical,  color: "text-red-400",    bg: "bg-red-950" },
            { label: "Resolution", value: `${resRate}%`,    color: "text-indigo-400", bg: "bg-indigo-950" },
          ].map(c => (
            <div key={c.label} className={`${c.bg} rounded-xl p-4 border border-gray-700`}>
              <div className="text-gray-400 text-xs uppercase tracking-wider">{c.label}</div>
              <div className={`text-3xl font-bold mt-1 ${c.color}`}>{c.value}</div>
            </div>
          ))}
        </div>

        {/* Escalated banner */}
        {totals.escalated > 0 && (
          <div className="bg-orange-950 border border-orange-700 rounded-xl px-5 py-3 mb-6 flex items-center gap-3">
            <span className="text-orange-400 text-xl">⚠️</span>
            <span className="text-orange-200"><strong>{totals.escalated}</strong> tickets escalated and need attention</span>
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
            <h2 className="text-lg font-semibold mb-4">By Category</h2>
            {by_category.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={by_category} dataKey="count" nameKey="category" cx="50%" cy="50%" outerRadius={90}
                    label={({ category, percent }: any) => `${category} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                    {by_category.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#1f2937", border: "none" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : <div className="text-gray-500 text-center py-20">No category data</div>}
          </div>

          <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
            <h2 className="text-lg font-semibold mb-4">By Priority</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={by_priority} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <XAxis dataKey="priority" stroke="#9ca3af" tick={{ fill: "#9ca3af" }} />
                <YAxis stroke="#9ca3af" tick={{ fill: "#9ca3af" }} />
                <Tooltip contentStyle={{ background: "#1f2937", border: "none" }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {by_priority.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="flex gap-4 flex-wrap">
          <a href="/tickets"    className="bg-indigo-600 hover:bg-indigo-700 px-6 py-3 rounded-lg font-medium transition">View All Tickets →</a>
          <a href="/resolve"    className="bg-emerald-700 hover:bg-emerald-600 px-6 py-3 rounded-lg font-medium transition">🤖 Batch AI Resolver →</a>
          <a href="/evaluation" className="bg-purple-700 hover:bg-purple-600 px-6 py-3 rounded-lg font-medium transition">📊 AI Evaluation →</a>
          <a href="/demo"       className="bg-gray-700 hover:bg-gray-600 px-6 py-3 rounded-lg font-medium transition">⚡ Live AI Demo →</a>
        </div>
      </div>
    </div>
  );
}
