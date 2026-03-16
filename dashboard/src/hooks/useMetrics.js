import { useState, useEffect } from "react";

const TIMESERIES_URL = "/metrics/timeseries";
const SUMMARY_URL = "/metrics/summary";
const LATEST_URL = "/metrics/latest";

export default function useMetrics() {
  const [state, setState] = useState({
    timeseries: null,
    summary: null,
    latest: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function fetchInitial() {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const [timeseriesRes, summaryRes, latestRes] = await Promise.all([
          fetch(TIMESERIES_URL),
          fetch(SUMMARY_URL),
          fetch(LATEST_URL),
        ]);
        if (!timeseriesRes.ok) throw new Error(timeseriesRes.statusText || "Timeseries fetch failed");
        if (!summaryRes.ok) throw new Error(summaryRes.statusText || "Summary fetch failed");
        const [timeseries, summary, latest] = await Promise.all([
          timeseriesRes.json(),
          summaryRes.json(),
          latestRes.ok ? latestRes.json() : Promise.resolve(null),
        ]);
        if (cancelled) return;
        setState((prev) => ({
          ...prev,
          timeseries: Array.isArray(timeseries) ? timeseries : [],
          summary,
          latest: latest ?? null,
          loading: false,
          error: null,
        }));
      } catch (e) {
        if (!cancelled) {
          setState((prev) => ({
            ...prev,
            timeseries: null,
            summary: null,
            latest: null,
            loading: false,
            error: e?.message ?? "Failed to load metrics",
          }));
        }
      }
    }

    fetchInitial();

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
