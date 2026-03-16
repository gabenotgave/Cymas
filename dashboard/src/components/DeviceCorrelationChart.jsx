import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";
import { THRESHOLDS } from "../constants/thresholds";

const BLUE = "#3b82f6";

function toScatterPoints(data) {
  return data
    .filter((row) => row.device_count != null && row.http_ttfb_ms != null)
    .map((row) => ({ x: row.device_count, y: row.http_ttfb_ms }));
}

export default function DeviceCorrelationChart({ data }) {
  const points = toScatterPoints(data ?? []);
  if (points.length === 0) return null;

  const minOpacity = 0.25;
  const maxOpacity = 1;
  const step = (maxOpacity - minOpacity) / Math.max(points.length, 1);

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
      <h2 className="text-gray-700 font-medium text-sm mb-4">Device count vs TTFB — correlation view</h2>
      <ResponsiveContainer width="100%" height={260}>
        <ScatterChart margin={{ top: 8, right: 16, left: 32, bottom: 32 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            type="number"
            dataKey="x"
            name="devices"
            label={{
              value: "devices on network",
              position: "insideBottom",
              offset: -6,
              fontSize: 11,
              fill: "#6b7280",
            }}
            stroke="#9ca3af"
            fontSize={11}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="TTFB"
            label={{ value: "TTFB (ms)", angle: -90, position: "insideLeft", fontSize: 11, fill: "#6b7280" }}
            stroke="#9ca3af"
            fontSize={11}
          />
          <ReferenceLine
            y={THRESHOLDS.TTFB_WARN_MS}
            stroke="#ef4444"
            strokeDasharray="4 4"
          />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            formatter={(val, name) => [val, name === "x" ? "Devices" : "TTFB (ms)"]}
            content={({ active, payload }) => {
              if (!active || !payload?.[0]) return null;
              const p = payload[0].payload;
              return (
                <div className="bg-white rounded-lg shadow-md border border-gray-100 p-2 text-xs">
                  <div className="text-gray-500">Devices: {p.x}</div>
                  <div className="text-gray-800 font-medium">TTFB: {p.y != null ? Number(p.y).toFixed(1) : "—"} ms</div>
                </div>
              );
            }}
          />
          <Scatter name="samples" data={points}>
            {points.map((_, index) => {
              const opacity = minOpacity + index * step;
              return <Cell key={index} fill={BLUE} fillOpacity={opacity} />;
            })}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <p className="text-gray-400 text-xs mt-2 italic">
        Each dot is one sample. More dots over time reveal whether device count predicts slowdowns.
      </p>
    </div>
  );
}
