from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LOG_PATH = Path("data/logs.jsonl")


def _pct(arr: list[float | int], q: float) -> float:
    if not arr:
        return 0.0
    sorted_arr = sorted(arr)
    idx = (len(sorted_arr) - 1) * (q / 100.0)
    floor = int(idx)
    ceil = min(floor + 1, len(sorted_arr) - 1)
    return round(float(sorted_arr[floor] + (sorted_arr[ceil] - sorted_arr[floor]) * (idx - floor)), 1)


def get_dashboard_metrics() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if LOG_PATH.exists():
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue

    responses = [r for r in records if r.get("event") == "response_sent"]
    requests = [r for r in records if r.get("event") == "request_received"]
    failures = [r for r in records if r.get("event") == "request_failed"]

    latencies = [float(r["latency_ms"]) for r in responses if "latency_ms" in r]
    ttfts = [float(r["ttft_ms"]) for r in responses if "ttft_ms" in r]

    p50 = _pct(latencies, 50)
    p95 = _pct(latencies, 95)
    p99 = _pct(latencies, 99)
    ttft_p95 = _pct(ttfts, 95)

    req_count = len(requests)
    rate_per_min = round(req_count / 60.0, 2) if req_count else 0.0

    error_rate = round((len(failures) / req_count * 100.0), 2) if req_count else 0.0
    tool_successes = [r for r in responses if r.get("tool_success") is True]
    tool_total = [r for r in records if r.get("tool_success") is not None]
    retrieval_success_rate = round((len(tool_successes) / len(tool_total) * 100.0), 1) if tool_total else 100.0

    cost_total = round(sum(float(r.get("cost_usd", 0.0)) for r in responses), 4)
    tokens_in = sum(int(r.get("tokens_in", 0)) for r in responses)
    tokens_out = sum(int(r.get("tokens_out", 0)) for r in responses)
    tokens_total = tokens_in + tokens_out

    quality_scores = [float(r["quality_score"]) for r in responses if "quality_score" in r]
    quality_mean = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.0

    # Error breakdown
    error_counts: dict[str, int] = {}
    for f in failures:
        etype = f.get("error_type", "Unknown")
        error_counts[etype] = error_counts.get(etype, 0) + 1

    return {
        "title": "K4-L3B Day 13 Monitoring & LLMOps",
        "time_range_minutes": 60,
        "refresh_seconds": 30,
        "total_records": len(records),
        "latency": {
            "p50": p50,
            "p95": p95,
            "p99": p99,
            "ttft_p95": ttft_p95,
            "unit": "ms",
            "threshold_p95": 3000,
            "status": "PASS" if p95 <= 3000 else "ALERT",
        },
        "traffic": {
            "count": req_count,
            "rate_per_minute": rate_per_min,
            "unit": "requests_per_minute",
            "threshold": 1.0,
            "status": "PASS" if rate_per_min >= 0.1 else "IDLE",
        },
        "errors": {
            "error_rate_pct": error_rate,
            "retrieval_success_rate_pct": retrieval_success_rate,
            "breakdown": error_counts,
            "unit": "percent",
            "threshold_error_rate": 2.0,
            "threshold_retrieval": 90.0,
            "status": "PASS" if error_rate <= 2.0 and retrieval_success_rate >= 90.0 else "ALERT",
        },
        "cost": {
            "total_usd": cost_total,
            "unit": "usd",
            "threshold": 2.5,
            "status": "PASS" if cost_total <= 2.5 else "ALERT",
        },
        "tokens": {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "total": tokens_total,
            "unit": "tokens",
            "threshold": 50000,
            "status": "PASS" if tokens_total <= 50000 else "ALERT",
        },
        "quality": {
            "mean": quality_mean,
            "unit": "score_0_to_1",
            "threshold": 0.75,
            "status": "PASS" if quality_mean >= 0.75 else "ALERT",
        },
    }


def render_dashboard_html() -> str:
    m = get_dashboard_metrics()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="30">
  <title>K4-L3B Day 13 Monitoring Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>body {{ font-family: 'Inter', sans-serif; }}</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-6">
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <header class="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4 mb-6">
      <div>
        <div class="flex items-center gap-3">
          <span class="inline-block w-3 h-3 rounded-full bg-emerald-400 animate-pulse"></span>
          <h1 class="text-2xl font-bold text-white tracking-tight">K4-L3B Day 13 Monitoring & LLMOps</h1>
        </div>
        <p class="text-sm text-slate-400 mt-1">Student: <span class="font-mono text-cyan-400">2A202602576</span> | Source: <span class="font-mono text-slate-300">data/logs.jsonl</span> ({m['total_records']} logs)</p>
      </div>
      <div class="flex items-center gap-3">
        <span class="bg-slate-800 text-slate-300 text-xs px-3 py-1.5 rounded-md border border-slate-700">Time Range: <b>Last 60m</b></span>
        <span class="bg-slate-800 text-cyan-400 text-xs px-3 py-1.5 rounded-md border border-slate-700">Refresh: <b>30s</b></span>
      </div>
    </header>

    <!-- 6 Panels Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      
      <!-- Panel 1: Latency -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-base font-semibold text-slate-200">1. Latency & TTFT</h2>
            <span class="text-xs font-semibold px-2 py-0.5 rounded {'bg-emerald-950 text-emerald-400 border border-emerald-800' if m['latency']['status'] == 'PASS' else 'bg-rose-950 text-rose-400 border border-rose-800'}">{m['latency']['status']}</span>
          </div>
          <div class="grid grid-cols-2 gap-3 my-3">
            <div class="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span class="text-xs text-slate-400">P50 Latency</span>
              <p class="text-2xl font-bold text-white mt-1">{m['latency']['p50']}<span class="text-xs font-normal text-slate-400 ml-1">ms</span></p>
            </div>
            <div class="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span class="text-xs text-slate-400">P95 Latency</span>
              <p class="text-2xl font-bold {'text-rose-400' if m['latency']['p95'] > 3000 else 'text-emerald-400'} mt-1">{m['latency']['p95']}<span class="text-xs font-normal text-slate-400 ml-1">ms</span></p>
            </div>
            <div class="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span class="text-xs text-slate-400">P99 Latency</span>
              <p class="text-xl font-bold text-slate-300 mt-1">{m['latency']['p99']}<span class="text-xs font-normal text-slate-400 ml-1">ms</span></p>
            </div>
            <div class="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span class="text-xs text-slate-400">TTFT P95</span>
              <p class="text-xl font-bold text-cyan-400 mt-1">{m['latency']['ttft_p95']}<span class="text-xs font-normal text-slate-400 ml-1">ms</span></p>
            </div>
          </div>
        </div>
        <p class="text-xs text-slate-400 pt-2 border-t border-slate-800/80 flex justify-between">
          <span>Threshold: P95 &le; 3000ms</span>
          <span class="text-slate-400">Unit: ms</span>
        </p>
      </div>

      <!-- Panel 2: Traffic -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-base font-semibold text-slate-200">2. Request Traffic</h2>
            <span class="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">{m['traffic']['status']}</span>
          </div>
          <div class="grid grid-cols-2 gap-3 my-3">
            <div class="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span class="text-xs text-slate-400">Total Requests</span>
              <p class="text-3xl font-bold text-white mt-1">{m['traffic']['count']}</p>
            </div>
            <div class="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span class="text-xs text-slate-400">Rate / Minute</span>
              <p class="text-3xl font-bold text-cyan-400 mt-1">{m['traffic']['rate_per_minute']}</p>
            </div>
          </div>
        </div>
        <p class="text-xs text-slate-400 pt-2 border-t border-slate-800/80 flex justify-between">
          <span>Threshold: Rate &ge; 1 req/min</span>
          <span class="text-slate-400">Unit: requests_per_minute</span>
        </p>
      </div>

      <!-- Panel 3: Errors & Retrieval -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-base font-semibold text-slate-200">3. Errors & Retrieval</h2>
            <span class="text-xs font-semibold px-2 py-0.5 rounded {'bg-emerald-950 text-emerald-400 border border-emerald-800' if m['errors']['status'] == 'PASS' else 'bg-rose-950 text-rose-400 border border-rose-800'}">{m['errors']['status']}</span>
          </div>
          <div class="grid grid-cols-2 gap-3 my-3">
            <div class="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span class="text-xs text-slate-400">Error Rate</span>
              <p class="text-3xl font-bold {'text-rose-400' if m['errors']['error_rate_pct'] > 2 else 'text-emerald-400'} mt-1">{m['errors']['error_rate_pct']}<span class="text-sm font-normal text-slate-400 ml-1">%</span></p>
            </div>
            <div class="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span class="text-xs text-slate-400">Retrieval Success</span>
              <p class="text-3xl font-bold text-emerald-400 mt-1">{m['errors']['retrieval_success_rate_pct']}<span class="text-sm font-normal text-slate-400 ml-1">%</span></p>
            </div>
          </div>
        </div>
        <p class="text-xs text-slate-400 pt-2 border-t border-slate-800/80 flex justify-between">
          <span>Threshold: Error &le; 2% | RAG &ge; 90%</span>
          <span class="text-slate-400">Unit: percent</span>
        </p>
      </div>

      <!-- Panel 4: Cost -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-base font-semibold text-slate-200">4. Cost Over Time</h2>
            <span class="text-xs font-semibold px-2 py-0.5 rounded {'bg-emerald-950 text-emerald-400 border border-emerald-800' if m['cost']['status'] == 'PASS' else 'bg-rose-950 text-rose-400 border border-rose-800'}">{m['cost']['status']}</span>
          </div>
          <div class="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80 my-3">
            <span class="text-xs text-slate-400">Total Cost (Last 60m)</span>
            <p class="text-3xl font-bold text-amber-400 mt-1">${m['cost']['total_usd']:.4f}<span class="text-xs font-normal text-slate-400 ml-2">USD</span></p>
            <div class="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
              <div class="bg-amber-400 h-full rounded-full" style="width: {min(100.0, (m['cost']['total_usd'] / 2.5) * 100)}%"></div>
            </div>
          </div>
        </div>
        <p class="text-xs text-slate-400 pt-2 border-t border-slate-800/80 flex justify-between">
          <span>Threshold: Total &le; $2.50</span>
          <span class="text-slate-400">Unit: usd</span>
        </p>
      </div>

      <!-- Panel 5: Tokens -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-base font-semibold text-slate-200">5. Input & Output Tokens</h2>
            <span class="text-xs font-semibold px-2 py-0.5 rounded {'bg-emerald-950 text-emerald-400 border border-emerald-800' if m['tokens']['status'] == 'PASS' else 'bg-rose-950 text-rose-400 border border-rose-800'}">{m['tokens']['status']}</span>
          </div>
          <div class="grid grid-cols-2 gap-3 my-3">
            <div class="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span class="text-xs text-slate-400">Tokens In</span>
              <p class="text-2xl font-bold text-sky-400 mt-1">{m['tokens']['tokens_in']:,}</p>
            </div>
            <div class="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
              <span class="text-xs text-slate-400">Tokens Out</span>
              <p class="text-2xl font-bold text-indigo-400 mt-1">{m['tokens']['tokens_out']:,}</p>
            </div>
          </div>
          <p class="text-xs text-slate-400 text-center">Total: <b>{m['tokens']['total']:,}</b> tokens</p>
        </div>
        <p class="text-xs text-slate-400 pt-2 border-t border-slate-800/80 flex justify-between">
          <span>Threshold: Total &le; 50,000</span>
          <span class="text-slate-400">Unit: tokens</span>
        </p>
      </div>

      <!-- Panel 6: Quality Proxy -->
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-base font-semibold text-slate-200">6. Quality Proxy</h2>
            <span class="text-xs font-semibold px-2 py-0.5 rounded {'bg-emerald-950 text-emerald-400 border border-emerald-800' if m['quality']['status'] == 'PASS' else 'bg-rose-950 text-rose-400 border border-rose-800'}">{m['quality']['status']}</span>
          </div>
          <div class="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80 my-3 text-center">
            <span class="text-xs text-slate-400">Mean Quality Score</span>
            <p class="text-4xl font-extrabold text-emerald-400 mt-1">{m['quality']['mean']}<span class="text-sm font-normal text-slate-400 ml-1">/ 1.0</span></p>
            <div class="w-full bg-slate-800 h-2 rounded-full mt-3 overflow-hidden">
              <div class="bg-emerald-400 h-full rounded-full" style="width: {m['quality']['mean'] * 100}%"></div>
            </div>
          </div>
        </div>
        <p class="text-xs text-slate-400 pt-2 border-t border-slate-800/80 flex justify-between">
          <span>Threshold: Mean &ge; 0.75</span>
          <span class="text-slate-400">Unit: score_0_to_1</span>
        </p>
      </div>

    </div>
  </div>
</body>
</html>
"""