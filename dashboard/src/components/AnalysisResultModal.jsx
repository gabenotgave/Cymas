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


  const parseReport = (text) => {
    const sections = { summary: "", findings: [], weakSignals: [], recommendations: [] };
    if (!text) return sections;

    const summaryMatch = text.match(/SUMMARY\n([\s\S]*?)(?=FINDINGS|WEAK SIGNALS|RECOMMENDATIONS|$)/i);
    const findingsMatch = text.match(/FINDINGS\n([\s\S]*?)(?=WEAK SIGNALS|RECOMMENDATIONS|$)/i);
    const weakSignalsMatch = text.match(/WEAK SIGNALS\n([\s\S]*?)(?=RECOMMENDATIONS|$)/i);
    const recommendationsMatch = text.match(/RECOMMENDATIONS\n([\s\S]*?)$/i);

    if (summaryMatch) sections.summary = summaryMatch[1].trim();

    const parseBlocks = (content) => {
      if (!content || content.trim().toLowerCase() === "none.") return [];
      return content.split(/FINDING:/i).filter(b => b.trim()).map(block => {
        const getField = (label) => {
          const match = block.match(new RegExp(`${label}:\\s*(.*)`, 'i'));
          return match ? match[1].trim() : "";
        };
        const findingMatch = block.match(/^([\s\S]*?)(?=METRICS:|TIME:|CONFIDENCE:|$)/i);
        return {
          finding: findingMatch ? findingMatch[1].trim() : "",
          metrics: getField("METRICS"),
          time: getField("TIME"),
          confidence: getField("CONFIDENCE")
        };
      }).filter(f => f.finding && f.finding.toLowerCase() !== "none.");
    };

    if (findingsMatch) sections.findings = parseBlocks(findingsMatch[1]);
    if (weakSignalsMatch) sections.weakSignals = parseBlocks(weakSignalsMatch[1]);
    
    if (recommendationsMatch) {
      const recContent = recommendationsMatch[1].trim();
      if (recContent.toLowerCase() !== "none.") {
        sections.recommendations = recContent.split(/ACTION:/i)
          .map(a => a.trim())
          .filter(a => a && a.toLowerCase() !== "none.");
      }
    }
    return sections;
  };

  const parsed = parseReport(result.summary);

  const getConfidenceStyles = (confidence) => {
    const c = (confidence || "").toLowerCase();
    if (c.includes("high")) return "text-emerald-700 bg-emerald-50 border-emerald-100";
    if (c.includes("medium")) return "text-amber-700 bg-amber-50 border-amber-100";
    if (c.includes("low")) return "text-blue-700 bg-blue-50 border-blue-100";
    return "text-gray-600 bg-gray-50 border-gray-100";
  };

  const Card = ({ item, isWeak }) => (
    <div className={`p-4 rounded-xl border mb-4 ${isWeak ? 'bg-gray-50/50 border-gray-100' : 'bg-white border-gray-100 shadow-sm'}`}>
      <p className="text-gray-900 font-medium text-sm mb-3">{item.finding}</p>
      <div className="grid grid-cols-1 gap-2 text-xs">
        <div className="flex gap-3">
          <span className="text-gray-400 w-24 shrink-0 font-medium uppercase tracking-wider">Metrics</span>
          <span className="text-gray-600">{item.metrics || "—"}</span>
        </div>
        <div className="flex gap-3">
          <span className="text-gray-400 w-24 shrink-0 font-medium uppercase tracking-wider">Time</span>
          <span className="text-gray-600">{item.time || "—"}</span>
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-gray-400 w-24 shrink-0 font-medium uppercase tracking-wider">Confidence</span>
          <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold uppercase tracking-tight ${getConfidenceStyles(item.confidence)}`}>
            {item.confidence || "Unknown"}
          </span>
        </div>
      </div>
    </div>
  );

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
        className="bg-white rounded-2xl shadow-xl w-full max-w-2xl mx-4 flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BrainCircuit size={16} className="text-gray-400" />
            <h2 className="text-gray-800 font-medium text-base">Network Diagnosis</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 px-6 py-6 scrollbar-hide">
          <section className="mb-8">
            <div className="text-gray-400 text-[10px] font-bold uppercase tracking-[0.1em] mb-3">Summary</div>
            <p className="text-gray-600 text-sm leading-relaxed">{parsed.summary || "No summary available."}</p>
          </section>

          <section className="mb-8">
            <div className="text-gray-400 text-[10px] font-bold uppercase tracking-[0.1em] mb-3">Findings</div>
            {parsed.findings.length > 0 ? (
              parsed.findings.map((f, i) => <Card key={i} item={f} />)
            ) : (
              <p className="text-gray-400 text-sm italic">None.</p>
            )}
          </section>

          {parsed.weakSignals.length > 0 && (
            <section className="mb-8">
              <div className="text-gray-400 text-[10px] font-bold uppercase tracking-[0.1em] mb-3">Weak Signals</div>
              {parsed.weakSignals.map((f, i) => <Card key={i} item={f} isWeak />)}
            </section>
          )}

          <section className="mb-4">
            <div className="text-gray-400 text-[10px] font-bold uppercase tracking-[0.1em] mb-3">Recommendations</div>
            {parsed.recommendations.length > 0 ? (
              <ul className="space-y-3">
                {parsed.recommendations.map((r, i) => (
                  <li key={i} className="flex gap-3 text-sm text-gray-600 items-start">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <span className="leading-relaxed">{r}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400 text-sm italic">None.</p>
            )}
          </section>
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

