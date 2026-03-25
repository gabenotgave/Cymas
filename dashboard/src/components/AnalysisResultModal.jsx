import { useState } from "react";
import { BrainCircuit, X } from "lucide-react";

export default function AnalysisResultModal({ result, onClose }) {
  const [copied, setCopied] = useState(false);

  if (!result) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose?.();
    }
  };

  const lines = String(result.summary || "").split("\n");

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.summary || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore clipboard errors
    }
  };

  const metaSamples = result?.stats?.total_samples ?? 0;
  const metaDuration = result?.stats?.duration_minutes ?? "—";
  const metaAnomalies = result?.anomaly_count ?? 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={handleBackdropClick}
    >
      <div
        className="dark:bg-zinc-800 bg-white rounded-2xl shadow-xl w-full max-w-2xl mx-4 flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b dark:border-zinc-700 border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BrainCircuit size={16} className="text-gray-400 dark:text-gray-100" />
            <h2 className="text-gray-800 dark:text-gray-100 font-medium text-base">Network Diagnosis</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 dark:text-gray-100 hover:text-gray-600 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 px-6 py-5">
          {lines.map((line, idx) => {
            const trimmed = line.trim();
            if (!trimmed) {
              return <div key={idx} className="mb-2" />;
            }

            if (trimmed === "Summary" || trimmed === "Findings" || trimmed === "Recommendations") {
              return (
                <div key={idx} className="text-gray-800 dark:text-gray-100 font-medium text-sm mt-4 mb-1">
                  {trimmed}
                </div>
              );
            }

            const bulletLike =
              /^[0-9]+\./.test(trimmed) || trimmed.startsWith("-") || trimmed.startsWith("•");

            if (bulletLike) {
              return (
                <div key={idx} className="text-gray-600 text-sm ml-3 leading-relaxed">
                  {trimmed}
                </div>
              );
            }

            return (
              <div key={idx} className="text-gray-600 text-sm leading-relaxed">
                {trimmed}
              </div>
            );
          })}
        </div>

        <div className="border-t border-gray-100 px-6 py-4 flex items-center justify-between">
          <div className="text-gray-400 text-xs">
            {metaAnomalies} anomalies detected · {metaSamples} samples · {metaDuration} min
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg px-3 py-1.5 transition-colors"
            >
              {copied ? "Copied!" : "Copy report"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="text-sm bg-black hover:bg-gray-800 text-white rounded-lg px-3 py-1.5 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

