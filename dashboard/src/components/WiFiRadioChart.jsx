import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { THRESHOLDS } from "../constants/thresholds";

const BLUE = "#3b82f6";
const EMERALD = "#10b981";

function formatTime(val) {
  try {
    return new Date(val).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return val;
  }
}

export default function WiFiRadioChart({ data }) {
  if (!data?.length) return null;

  return (
    <div className="dark:bg-zinc-800 bg-white rounded-2xl shadow-sm border dark:border-zinc-700 border-gray-100 p-5">
      <h2 className="text-gray-700 dark:text-gray-100 font-medium text-sm mb-4">WiFi radio health</h2>
      <div className="flex gap-4 mb-3">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: BLUE }} />
          <span className="text-gray-500 text-xs">SNR (dB)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: EMERALD }} />
          <span className="text-gray-500 text-xs">TX rate (Mbps)</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatTime}
            stroke="#9ca3af"
            fontSize={11}
          />
          <YAxis stroke="#9ca3af" fontSize={11} tickFormatter={(v) => (v != null ? String(v) : "")} />
          <YAxis yAxisId="right" orientation="right" stroke="#9ca3af" fontSize={11} />
          <ReferenceLine
            y={THRESHOLDS.SNR_WARN_DB}
            stroke="#fbbf24"
            strokeDasharray="4 4"
            label={{ value: "min healthy", position: "right", fontSize: 10, fill: "#9ca3af" }}
          />
          <Area
            type="monotone"
            dataKey="wifi_snr_db"
            name="SNR (dB)"
            stroke={BLUE}
            fill={BLUE}
            fillOpacity={0.15}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="wifi_tx_rate_mbps"
            name="TX rate (Mbps)"
            yAxisId="right"
            stroke={EMERALD}
            dot={false}
            strokeWidth={2}
            connectNulls={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
