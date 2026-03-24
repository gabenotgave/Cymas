import { THRESHOLDS } from "../constants/thresholds";

function cardBorder(avg, threshold, highIsGood = false) {
  if (threshold == null) return "border-gray-200";
  if (avg == null) return "border-gray-200";
  if (highIsGood) {
    return avg >= threshold ? "border-emerald-500" : "border-amber-400";
  }
  return avg > threshold ? "border-amber-400" : "border-emerald-500";
}

function formatVal(val) {
  if (val == null || val === "") return "—";
  const n = Number(val);
  if (Number.isNaN(n)) return "—";
  return n.toFixed(1);
}

export default function StatCards({ summary }) {
  if (summary == null) return null;

  const ttfb = summary.http_ttfb_ms?.mean;
  const gwPing = summary.ping_gateway_avg_ms?.mean;
  const extPing = summary.ping_external_avg_ms?.mean;
  const snr = summary.wifi_snr_db?.mean;
  const devices = summary.device_count?.mean;
  const total = summary.total_samples ?? 0;

  const cards = [
    { label: "AVG TTFB", value: formatVal(ttfb), unit: "ms", border: cardBorder(ttfb, THRESHOLDS.TTFB_WARN_MS) },
    { label: "AVG GATEWAY PING", value: formatVal(gwPing), unit: "ms", border: cardBorder(gwPing, THRESHOLDS.PING_WARN_MS) },
    { label: "AVG EXTERNAL PING", value: formatVal(extPing), unit: "ms", border: cardBorder(extPing, THRESHOLDS.PING_WARN_MS) },
    { label: "AVG SNR", value: formatVal(snr), unit: "dB", border: cardBorder(snr, THRESHOLDS.SNR_WARN_DB, true) },
    { label: "AVG DEVICE COUNT", value: formatVal(devices), unit: "", border: "border-gray-200" },
    { label: "TOTAL SAMPLES", value: String(total), unit: "", border: "border-blue-400" },
  ];

  return (
    <div className="dark:bg-zinc-800 bg-white grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map(({ label, value, unit, border }) => (
        <div
          key={label}
          className={` rounded-2xl shadow-sm border dark:border-gray-700 border-gray-100 border-l-4 ${border} p-5`}
        >
          <div className="text-gray-500 text-xs tracking-wide uppercase">{label}</div>
          <div className="text-2xl font-medium text-gray-800 mt-1">{value}</div>
          {unit && <div className="text-gray-400 text-xs mt-0.5">{unit}</div>}
        </div>
      ))}
    </div>
  );
}
