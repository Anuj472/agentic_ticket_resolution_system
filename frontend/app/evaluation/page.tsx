"use client";
import { useEffect, useState } from "react";
import { apiCall } from "@/lib/api";

interface EvalResults {
  run_at: string;
  classification: {
    accuracy_pct: number; macro_f1: number; total_samples: number; correct: number;
    f1_per_class: Record<string, number>;
    predictions: string[]; ground_truth: string[];
  };
  semantic_similarity: { mean: number; min: number; max: number; samples: number };
  llm_judge: {
    mean_relevance: number; mean_correctness: number;
    mean_completeness: number; mean_overall: number; sample_size: number;
    details: Array<{ relevance: number; correctness: number; completeness: number; overall: number; feedback: string }>;
  };
  summary: { accuracy_pct: number; macro_f1: number; semantic_similarity: number; llm_judge_overall: number };
}

const CATEGORIES = ["Infrastructure", "Application", "Security", "Database", "Network", "Access Management"];

function ScoreBar({ value, max = 10, color }: { value: number; max?: number; color: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full bg-gray-800 rounded-full h-2 mt-1">
      <div className={`h-2 rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

function MetricCard({ icon, label, value, unit, sub, color, barMax }:
  { icon: string; label: string; value: number; unit: string; sub: string; color: string; barMax?: number }) {
  return (
    <div className={`bg-gray-800/70 border rounded-2xl p-5 ${color}`}>
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-gray-400 text-xs uppercase tracking-wider">{label}</div>
      <div className="text-3xl font-bold mt-1">{value}{unit}</div>
      <ScoreBar value={value} max={barMax ?? 100} color={color.replace("border-", "bg-").split(" ")[0]} />
      <div className="text-gray-500 text-xs mt-2">{sub}</div>
    </div>
  );
}

export default function EvaluationPage() {
  const [results,  setResults]  = useState<EvalResults | null>(null);
  const [running,  setRunning]  = useState(false);
  const [polling,  setPolling]  = useState(false);
  const [error,    setError]    = useState("");
  const [tab,      setTab]      = useState<"overview" | "classification" | "judge">("overview");

  useEffect(() => { fetchResults(); }, []);

  async function fetchResults() {
    try {
      const data = await apiCall<EvalResults>("GET", "/evaluation/results");
      setResults(data);
    } catch (_) { /* no results yet */ }
  }

  async function runEval() {
    setRunning(true); setError("");
    try {
      await apiCall("POST", "/evaluation/run");
      setPolling(true);
      // Poll every 5s until results appear
      const interval = setInterval(async () => {
        try {
          const data = await apiCall<EvalResults>("GET", "/evaluation/results");
          if (data) { setResults(data); setPolling(false); setRunning(false); clearInterval(interval); }
        } catch (_) {}
      }, 5000);
      // Stop polling after 3 minutes
      setTimeout(() => { clearInterval(interval); setRunning(false); setPolling(false); }, 180_000);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message);
      setRunning(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/70 backdrop-blur-md sticky top-0 z-10 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">📊 AI Model Evaluation</h1>
            <p className="text-gray-400 text-sm">Accuracy · F1 Score · Semantic Similarity · LLM-as-Judge</p>
          </div>
          <div className="flex items-center gap-3">
            {results && (
              <span className="text-xs text-gray-500">
                Last run: {new Date(results.run_at).toLocaleString()}
              </span>
            )}
            <button onClick={runEval} disabled={running}
              className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 px-5 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-2">
              {running ? <><span className="animate-spin">⟳</span>{polling ? "Evaluating…" : "Starting…"}</> : "▶ Run Evaluation"}
            </button>
            <a href="/" className="text-indigo-400 hover:text-indigo-300 text-sm">← Dashboard</a>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {error && <div className="mb-4 bg-red-950/50 border border-red-700 rounded-xl px-4 py-3 text-red-300 text-sm">⚠️ {error}</div>}

        {running && !results && (
          <div className="flex flex-col items-center py-20 gap-4">
            <div className="text-5xl animate-pulse">🧪</div>
            <h2 className="text-xl font-bold">Evaluation in progress…</h2>
            <p className="text-gray-400 text-sm text-center">
              Running classification on 30 ground-truth tickets · Generating solutions · LLM judge scoring<br/>
              This takes approximately 60–90 seconds.
            </p>
            <div className="flex gap-1 mt-2">
              {[0,1,2].map(i => (
                <div key={i} className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: `${i*150}ms` }} />
              ))}
            </div>
          </div>
        )}

        {!results && !running && (
          <div className="flex flex-col items-center py-20 gap-4">
            <div className="text-5xl">📊</div>
            <h2 className="text-2xl font-bold">No evaluation results yet</h2>
            <p className="text-gray-400 text-center max-w-lg">
              Click <strong>Run Evaluation</strong> to benchmark the AI pipeline against
              30 labeled ground-truth tickets across all 6 categories.
            </p>
            <div className="grid grid-cols-2 gap-3 text-sm text-gray-500 bg-gray-900/40 border border-gray-800 rounded-xl p-5 max-w-md">
              <div>📐 <strong className="text-gray-300">Classification Accuracy</strong><br/>Correct category % on 30 test tickets</div>
              <div>📏 <strong className="text-gray-300">Macro F1 Score</strong><br/>Per-class F1 averaged across 6 categories</div>
              <div>🔗 <strong className="text-gray-300">Semantic Similarity</strong><br/>BGE cosine similarity of AI solutions</div>
              <div>🧑‍⚖️ <strong className="text-gray-300">LLM-as-Judge</strong><br/>GPT scores solutions 1–10 on 3 dimensions</div>
            </div>
          </div>
        )}

        {results && (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <MetricCard icon="🎯" label="Classification Accuracy" value={results.summary.accuracy_pct} unit="%" sub={`${results.classification.correct}/${results.classification.total_samples} correct`} color="border-green-700/50 text-green-400" barMax={100} />
              <MetricCard icon="📏" label="Macro F1 Score" value={Math.round(results.summary.macro_f1 * 100)} unit="%" sub="Averaged across 6 categories" color="border-blue-700/50 text-blue-400" barMax={100} />
              <MetricCard icon="🔗" label="Semantic Similarity" value={Math.round(results.summary.semantic_similarity * 100)} unit="%" sub={`${results.semantic_similarity.samples} solution pairs`} color="border-purple-700/50 text-purple-400" barMax={100} />
              <MetricCard icon="🧑‍⚖️" label="LLM Judge Score" value={results.summary.llm_judge_overall} unit="/10" sub={`${results.llm_judge.sample_size} tickets evaluated`} color="border-yellow-700/50 text-yellow-400" barMax={10} />
            </div>

            {/* Tabs */}
            <div className="flex gap-2 mb-5">
              {(["overview", "classification", "judge"] as const).map(t => (
                <button key={t} onClick={() => setTab(t)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${tab === t ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-400 hover:bg-gray-700"}`}>
                  {t === "overview" ? "📈 Overview" : t === "classification" ? "🏷️ Classification" : "🧑‍⚖️ LLM Judge"}
                </button>
              ))}
            </div>

            {/* Tab: Overview */}
            {tab === "overview" && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <div className="bg-gray-800/60 border border-gray-700 rounded-2xl p-5">
                  <h3 className="font-semibold text-sm text-gray-400 uppercase mb-4">F1 Score by Category</h3>
                  <div className="space-y-3">
                    {CATEGORIES.map(cat => {
                      const f1 = results.classification.f1_per_class[cat] ?? 0;
                      return (
                        <div key={cat}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-300">{cat}</span>
                            <span className="font-mono text-indigo-400">{(f1 * 100).toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-gray-700 rounded-full h-2">
                            <div className="h-2 rounded-full bg-indigo-500 transition-all duration-700"
                              style={{ width: `${f1 * 100}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
                <div className="bg-gray-800/60 border border-gray-700 rounded-2xl p-5">
                  <h3 className="font-semibold text-sm text-gray-400 uppercase mb-4">LLM Judge Dimensions</h3>
                  <div className="space-y-3">
                    {[
                      ["Relevance",    results.llm_judge.mean_relevance],
                      ["Correctness",  results.llm_judge.mean_correctness],
                      ["Completeness", results.llm_judge.mean_completeness],
                      ["Overall",      results.llm_judge.mean_overall],
                    ].map(([label, val]) => (
                      <div key={label as string}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-300">{label}</span>
                          <span className="font-mono text-yellow-400">{(val as number).toFixed(1)}/10</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div className="h-2 rounded-full bg-yellow-500 transition-all duration-700"
                            style={{ width: `${(val as number) * 10}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <div className="text-xs text-gray-500 mb-2">Semantic Similarity (BGE cosine)</div>
                    <div className="flex gap-4 text-sm">
                      <div><span className="text-gray-500">Mean</span> <span className="text-purple-400 font-mono">{(results.semantic_similarity.mean * 100).toFixed(1)}%</span></div>
                      <div><span className="text-gray-500">Min</span> <span className="text-gray-400 font-mono">{(results.semantic_similarity.min * 100).toFixed(1)}%</span></div>
                      <div><span className="text-gray-500">Max</span> <span className="text-gray-400 font-mono">{(results.semantic_similarity.max * 100).toFixed(1)}%</span></div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab: Classification detail */}
            {tab === "classification" && (
              <div className="bg-gray-800/60 border border-gray-700 rounded-2xl overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-700 flex items-center justify-between">
                  <h3 className="font-semibold">Prediction vs Ground Truth ({results.classification.total_samples} samples)</h3>
                  <span className="text-xs text-gray-500">gpt-4.1-nano + BGE centroid classifier</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-900/60">
                      <tr className="text-gray-500 text-xs uppercase">
                        <th className="text-left px-4 py-3">#</th>
                        <th className="text-left px-4 py-3">Ground Truth</th>
                        <th className="text-left px-4 py-3">AI Prediction</th>
                        <th className="text-left px-4 py-3">Match</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.classification.ground_truth.map((gt, i) => {
                        const pred = results.classification.predictions[i];
                        const match = pred === gt;
                        return (
                          <tr key={i} className={`border-t border-gray-800 ${match ? "" : "bg-red-950/10"}`}>
                            <td className="px-4 py-2 text-gray-600 font-mono text-xs">{i + 1}</td>
                            <td className="px-4 py-2 text-gray-300">{gt}</td>
                            <td className={`px-4 py-2 font-medium ${match ? "text-green-400" : "text-red-400"}`}>{pred}</td>
                            <td className="px-4 py-2">{match ? "✅" : "❌"}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab: LLM Judge detail */}
            {tab === "judge" && (
              <div className="space-y-3">
                {results.llm_judge.details?.map((d, i) => (
                  <div key={i} className="bg-gray-800/60 border border-gray-700 rounded-xl px-5 py-4">
                    <div className="flex items-center gap-4 flex-wrap mb-2">
                      <span className="text-gray-500 text-xs font-mono">#{i + 1}</span>
                      {[["Relevance", d.relevance], ["Correctness", d.correctness], ["Completeness", d.completeness], ["Overall", d.overall]].map(([l, v]) => (
                        <div key={l as string} className="text-sm">
                          <span className="text-gray-500">{l}: </span>
                          <span className={`font-bold ${(v as number) >= 7 ? "text-green-400" : (v as number) >= 5 ? "text-yellow-400" : "text-red-400"}`}>{v}/10</span>
                        </div>
                      ))}
                    </div>
                    {d.feedback && <p className="text-gray-400 text-sm italic">"{d.feedback}"</p>}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
