"use client";
import { useEffect, useState } from "react";
import axios from "axios";
import Link from "next/link";

const API = "/api/proxy";
const PSIZE = 20;

const PRIORITY_COLOR: Record<string, string> = {
  critical: "bg-red-900 text-red-300",
  high:     "bg-orange-900 text-orange-300",
  medium:   "bg-yellow-900 text-yellow-300",
  low:      "bg-gray-700 text-gray-300",
};
const STATUS_COLOR: Record<string, string> = {
  new:         "bg-blue-900 text-blue-300",
  in_progress: "bg-indigo-900 text-indigo-300",
  resolved:    "bg-green-900 text-green-300",
  closed:      "bg-gray-700 text-gray-300",
};

// BUG-07 FIX: Cache token in sessionStorage — only login once per browser session
async function getToken(): Promise<string> {
  const cached = sessionStorage.getItem("auth_token");
  if (cached) return cached;
  const r = await axios.post(`${API}/auth/login`, {
    email: "admin@company.com",
    password: "Admin@1234",
  });
  const token: string = r.data.access_token;
  sessionStorage.setItem("auth_token", token);
  return token;
}

async function fetchWithAuth(url: string) {
  const token = await getToken();
  try {
    return await axios.get(url, { headers: { Authorization: `Bearer ${token}` } });
  } catch (e: any) {
    // On 401 clear cache and retry once with a fresh token
    if (e?.response?.status === 401) {
      sessionStorage.removeItem("auth_token");
      const freshToken = await getToken();
      return axios.get(url, { headers: { Authorization: `Bearer ${freshToken}` } });
    }
    throw e;
  }
}

export default function TicketsPage() {
  const [tickets, setTickets] = useState<any[]>([]);
  const [total,   setTotal]   = useState(0);
  const [page,    setPage]    = useState(1);
  const [filter,  setFilter]  = useState({ priority: "", category: "" });
  const [error,   setError]   = useState("");

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), page_size: String(PSIZE) });
    if (filter.priority) params.append("priority", filter.priority);
    if (filter.category) params.append("category", filter.category);

    fetchWithAuth(`${API}/tickets/?${params}`)
      .then(r => { setTickets(r.data.items); setTotal(r.data.total); })
      .catch(e => setError(e?.response?.data?.detail || e.message));
  }, [page, filter]);

  const pages = Math.ceil(total / PSIZE);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">All Tickets</h1>
            <p className="text-gray-400">{total.toLocaleString()} total</p>
          </div>
          <a href="/" className="text-indigo-400 hover:text-indigo-300">← Dashboard</a>
        </div>

        {error && (
          <div className="bg-red-950 border border-red-700 rounded-xl px-4 py-3 mb-4 text-red-300 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-3 mb-5">
          {[
            ["priority", "critical", "high", "medium", "low"],
            ["category", "Application", "Infrastructure", "Access Management", "Network", "Database", "Security"],
          ].map(([key, ...opts]) => (
            <select
              key={key}
              onChange={e => { setFilter(f => ({ ...f, [key]: e.target.value })); setPage(1); }}
              className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="">All {key}s</option>
              {opts.map(o => <option key={o} value={o.toLowerCase()}>{o}</option>)}
            </select>
          ))}
        </div>

        {/* Table */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400 uppercase text-xs">
              <tr>
                {["Ticket", "Title", "Category", "Priority", "Status", "Created"].map(h => (
                  <th key={h} className="px-4 py-3 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {tickets.map(t => (
                <tr key={t.id} className="hover:bg-gray-750 transition">
                  <td className="px-4 py-3 font-mono text-indigo-400">
                    <Link href={`/tickets/${t.id}`} className="hover:underline">{t.ticket_number}</Link>
                  </td>
                  <td className="px-4 py-3 max-w-xs truncate">{t.title}</td>
                  <td className="px-4 py-3 text-gray-300">{t.category || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${PRIORITY_COLOR[t.priority] || "bg-gray-700"}`}>
                      {t.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${STATUS_COLOR[t.status] || "bg-gray-700"}`}>
                      {t.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{new Date(t.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {tickets.length === 0 && (
            <div className="text-center py-12 text-gray-500">No tickets found</div>
          )}
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <span className="text-gray-400 text-sm">Page {page} of {pages || 1}</span>
          <div className="flex gap-2">
            <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
              className="px-4 py-2 bg-gray-700 rounded-lg disabled:opacity-40 hover:bg-gray-600">← Prev</button>
            <button disabled={page === pages || pages === 0} onClick={() => setPage(p => p + 1)}
              className="px-4 py-2 bg-gray-700 rounded-lg disabled:opacity-40 hover:bg-gray-600">Next →</button>
          </div>
        </div>
      </div>
    </div>
  );
}
