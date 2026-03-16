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
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
      <h2 className="text-gray-700 font-medium text-sm mb-4">WiFi radio health</h2>
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
