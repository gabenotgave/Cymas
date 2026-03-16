import { useState, useEffect } from "react";
import { BrainCircuit, X } from "lucide-react";
import { THRESHOLDS } from "../constants/thresholds";
import AnalysisResultModal from "./AnalysisResultModal";

const PAGE_SIZE = 20;

function buildRawUrl(page, start, end) {
  const offset = (page - 1) * PAGE_SIZE;
  const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
  if (start?.trim()) params.set("start", start.trim());
  if (end?.trim()) params.set("end", end.trim());
  return `/metrics/raw?${params.toString()}`;
}

function formatVal(val) {
  if (val == null || val === "") return "—";
  if (typeof val === "number" && !Number.isNaN(val)) return val.toFixed(1);
  return String(val);
}

function cellClass(val, threshold, highIsGood = false) {
  if (val == null || val === "" || threshold == null) return "";
  const n = Number(val);
  if (Number.isNaN(n)) return "";
  if (highIsGood) {
    if (n < threshold) return "bg-red-50 text-red-700";
    if (n < threshold * 1.2) return "bg-amber-50 text-amber-700";
    return "";
  }
  if (n > threshold) return "bg-red-50 text-red-700";
  if (n > threshold * 0.8 && n <= threshold) return "bg-amber-50 text-amber-700";
  return "";
}

export default function RawTable() {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [startInput, setStartInput] = useState("");
  const [endInput, setEndInput] = useState("");
  const [appliedStart, setAppliedStart] = useState("");
  const [appliedEnd, setAppliedEnd] = useState("");
  const [page, setPage] = useState(1);
  const [resetting, setResetting] = useState(false);
  const [diagnosing, setDiagnosing] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState(null);
  const [diagnosisError, setDiagnosisError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const url = buildRawUrl(page, appliedStart, appliedEnd);
    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || "Raw fetch failed");
        return res.json();
      })
      .then((body) => {
        if (cancelled) return;
        const data = body?.data ?? [];
        setRows(Array.isArray(data) ? data : []);
        setTotal(typeof body?.total === "number" ? body.total : 0);
      })
      .catch((e) => {
        if (!cancelled) setError(e?.message ?? "Failed to load raw data");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [page, appliedStart, appliedEnd]);

  function handleFilterSubmit(e) {
    e.preventDefault();
    setPage(1);
    setAppliedStart(startInput.trim());
    setAppliedEnd(endInput.trim());
  }

  async function handleReset() {
    const ok = window.confirm(
      "Reset data? This will erase the metrics CSV on the server (cannot be undone)."
    );
    if (!ok) return;

    setResetting(true);
    setError(null);
    try {
      const res = await fetch("/metrics/reset", { method: "POST" });
      if (!res.ok) throw new Error(res.statusText || "Reset failed");
      setPage(1);
      setRows([]);
      setTotal(0);
    } catch (e) {
      setError(e?.message ?? "Failed to reset data");
    } finally {
      setResetting(false);
    }
  }

  const start = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const end = Math.min(page * PAGE_SIZE, total);
  const pageRows = rows;

  const hasRange = !!startInput && !!endInput;
  const invalidDiagnosisRange =
    (!hasRange && (startInput || endInput)) || // only one side filled
    (hasRange && startInput >= endInput);
  const diagnoseLabel = hasRange ? "Diagnose this range (AI)" : "Diagnose all data (AI)";

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-blue-500" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <p className="text-red-400 text-sm">{error}</p>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <div className="flex flex-col gap-3 mb-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <h2 className="text-gray-700 font-medium text-sm h-9 flex items-center">
              Raw samples
            </h2>
            <form
              className="flex flex-col sm:flex-row gap-3 sm:items-center"
              onSubmit={handleFilterSubmit}
            >
              <label className="flex items-center gap-2 h-9">
                <span className="text-gray-500 text-xs">Start</span>
                <input
                  type="datetime-local"
                  value={startInput}
                  onChange={(e) => setStartInput(e.target.value)}
                  className="border border-gray-200 rounded-lg text-sm px-3 h-9 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </label>
              <label className="flex items-center gap-2 h-9">
                <span className="text-gray-500 text-xs">End</span>
                <input
                  type="datetime-local"
                  value={endInput}
                  onChange={(e) => setEndInput(e.target.value)}
                  className="border border-gray-200 rounded-lg text-sm px-3 h-9 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </label>
              <button
                type="submit"
                disabled={loading}
                className="h-9 rounded-lg px-3 text-sm font-medium border border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Apply filter
              </button>
              <button
                type="button"
                onClick={() => {
                  setStartInput("");
                  setEndInput("");
                  setAppliedStart("");
                  setAppliedEnd("");
                  setPage(1);
                }}
                disabled={loading}
                className="h-9 rounded-lg px-3 text-sm font-normal border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Clear
              </button>
              <button
                type="button"
                onClick={handleReset}
                disabled={resetting || loading}
                className="h-9 rounded-lg px-3 text-sm font-medium border border-red-200 text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Erase the metrics CSV on the server"
              >
                {resetting ? "Resetting…" : "Reset data"}
              </button>
              <button
                type="button"
                disabled={invalidDiagnosisRange || diagnosing}
                onClick={async () => {
                  if (invalidDiagnosisRange || diagnosing) return;
                  setDiagnosing(true);
                  setDiagnosisResult(null);
                  setDiagnosisError(null);
                  try {
                    const res = await fetch("/analysis/run", {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                      },
                      body: JSON.stringify({
                        start_time: hasRange ? startInput : "",
                        end_time: hasRange ? endInput : "",
                      }),
                    });
                    const body = await res.json().catch(() => ({}));
                    if (!res.ok) {
                      const detail = body?.detail || "Failed to run analysis";
                      throw new Error(detail);
                    }
                    setDiagnosisResult(body);
                  } catch (e) {
                    setDiagnosisError(e?.message ?? "Failed to run analysis");
                  } finally {
                    setDiagnosing(false);
                  }
                }}
                className={`bg-black hover:bg-gray-800 text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors flex items-center gap-2 ${
                  invalidDiagnosisRange || diagnosing ? "opacity-50 cursor-not-allowed" : ""
                }`}
              >
                {diagnosing ? (
                  <>
                    <div className="h-3 w-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    <span>Diagnosing...</span>
                  </>
                ) : (
                  <>
                    <BrainCircuit size={15} />
                    <span>{diagnoseLabel}</span>
                  </>
                )}
              </button>
            </form>
          </div>
          {diagnosisError && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg px-3 py-2 flex items-center justify-between">
              <span>{diagnosisError}</span>
              <button
                type="button"
                onClick={() => setDiagnosisError(null)}
                className="ml-2 text-red-400 hover:text-red-600"
              >
                <X size={14} />
              </button>
            </div>
          )}
        </div>
        <div className="overflow-x-auto">
        <table className="w-full text-xs table-auto">
          <thead>
            <tr className="text-left text-gray-500 border-b border-gray-100">
              <th className="py-2 pr-2 font-medium">Timestamp</th>
              <th className="py-2 pr-2 font-medium">Devices</th>
              <th className="py-2 pr-2 font-medium">GW Ping</th>
              <th className="py-2 pr-2 font-medium">Ext Ping</th>
              <th className="py-2 pr-2 font-medium">DNS</th>
              <th className="py-2 pr-2 font-medium">TTFB</th>
              <th className="py-2 pr-2 font-medium">SSID</th>
              <th className="py-2 pr-2 font-medium">RSSI</th>
              <th className="py-2 pr-2 font-medium">SNR</th>
              <th className="py-2 pr-2 font-medium">Channel</th>
              <th className="py-2 pr-2 font-medium">TX Rate</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={i} className="border-b border-gray-50">
                <td className="py-1.5 pr-2 text-gray-800 font-normal">{formatVal(row.timestamp)}</td>
                <td className={`py-1.5 pr-2 font-normal ${cellClass(row.device_count, null)}`}>{row.device_count != null && row.device_count !== "" ? formatVal(row.device_count) : <span className="text-gray-300">—</span>}</td>
                <td className={`py-1.5 pr-2 font-normal ${cellClass(row.ping_gateway_avg_ms, THRESHOLDS.PING_WARN_MS)}`}>{row.ping_gateway_avg_ms != null && row.ping_gateway_avg_ms !== "" ? formatVal(row.ping_gateway_avg_ms) : <span className="text-gray-300">—</span>}</td>
                <td className={`py-1.5 pr-2 font-normal ${cellClass(row.ping_external_avg_ms, THRESHOLDS.PING_WARN_MS)}`}>{row.ping_external_avg_ms != null && row.ping_external_avg_ms !== "" ? formatVal(row.ping_external_avg_ms) : <span className="text-gray-300">—</span>}</td>
                <td className={`py-1.5 pr-2 font-normal ${cellClass(row.dns_resolution_ms, THRESHOLDS.DNS_WARN_MS)}`}>{row.dns_resolution_ms != null && row.dns_resolution_ms !== "" ? formatVal(row.dns_resolution_ms) : <span className="text-gray-300">—</span>}</td>
                <td className={`py-1.5 pr-2 font-normal ${cellClass(row.http_ttfb_ms, THRESHOLDS.TTFB_WARN_MS)}`}>{row.http_ttfb_ms != null && row.http_ttfb_ms !== "" ? formatVal(row.http_ttfb_ms) : <span className="text-gray-300">—</span>}</td>
                <td className="py-1.5 pr-2 font-normal text-gray-800">{row.wifi_ssid != null && row.wifi_ssid !== "" ? String(row.wifi_ssid) : <span className="text-gray-300">—</span>}</td>
                <td className="py-1.5 pr-2 font-normal text-gray-800">{row.wifi_rssi_dbm != null && row.wifi_rssi_dbm !== "" ? formatVal(row.wifi_rssi_dbm) : <span className="text-gray-300">—</span>}</td>
                <td className={`py-1.5 pr-2 font-normal ${cellClass(row.wifi_snr_db, THRESHOLDS.SNR_WARN_DB, true)}`}>{row.wifi_snr_db != null && row.wifi_snr_db !== "" ? formatVal(row.wifi_snr_db) : <span className="text-gray-300">—</span>}</td>
                <td className="py-1.5 pr-2 font-normal text-gray-800">{row.wifi_channel != null && row.wifi_channel !== "" ? formatVal(row.wifi_channel) : <span className="text-gray-300">—</span>}</td>
                <td className="py-1.5 pr-2 font-normal text-gray-800">{row.wifi_tx_rate_mbps != null && row.wifi_tx_rate_mbps !== "" ? formatVal(row.wifi_tx_rate_mbps) : <span className="text-gray-300">—</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
        <div className="flex items-center justify-center gap-4 mt-4">
        <button
          type="button"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page <= 1}
          className="text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        <span className="text-gray-500 text-sm">
          Showing {total === 0 ? 0 : start}–{end} of {total} results
        </span>
        <button
          type="button"
          onClick={() => setPage((p) => p + 1)}
          disabled={end >= total}
          className="text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
        </div>
      </div>
      <AnalysisResultModal
        result={diagnosisResult}
        onClose={() => setDiagnosisResult(null)}
      />
    </>
  );
}
