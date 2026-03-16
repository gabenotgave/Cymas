import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";
import { THRESHOLDS } from "../constants/thresholds";

const CACHE_HIT = "#10b981";
const FRESH_LOOKUP = "#8b5cf6";
const CACHE_THRESHOLD_MS = 3;

function formatTime(val) {
  try {
    return new Date(val).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return val;
  }
}

function barFill(ms) {
  if (ms == null) return "#e5e7eb";
  return ms < CACHE_THRESHOLD_MS ? CACHE_HIT : FRESH_LOOKUP;
}

export default function DnsChart({ data }) {
  if (!data?.length) return null;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
      <h2 className="text-gray-700 font-medium text-sm mb-4">DNS resolution</h2>
      <div className="flex gap-4 mb-3">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: CACHE_HIT }} />
          <span className="text-gray-500 text-xs">Cache hit (&lt; 3ms)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: FRESH_LOOKUP }} />
          <span className="text-gray-500 text-xs">Fresh lookup</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatTime}
            stroke="#9ca3af"
            fontSize={11}
          />
          <YAxis stroke="#9ca3af" fontSize={11} />
          <ReferenceLine
            y={THRESHOLDS.DNS_WARN_MS}
            stroke="#fbbf24"
            strokeDasharray="4 4"
            label={{ value: "warn", position: "right", fontSize: 10, fill: "#9ca3af" }}
          />
          <Bar dataKey="dns_resolution_ms" name="DNS (ms)" radius={[2, 2, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={index} fill={barFill(entry.dns_resolution_ms)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
