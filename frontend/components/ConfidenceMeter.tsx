"use client";

/**
 * Visual confidence indicator used everywhere the AI gives an answer.
 * Directly implements the "AI Explainability / Responsible AI" requirement:
 * every answer must visibly show how confident the system is, not just
 * the text of the answer.
 */
export default function ConfidenceMeter({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    score >= 0.65 ? "bg-maroon" : score >= 0.35 ? "bg-rose" : "bg-red-500";
  const label = score >= 0.65 ? "High confidence" : score >= 0.35 ? "Moderate confidence" : "Low confidence";

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs mb-1 text-maroon-dark/70">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-blush/50 overflow-hidden">
        <div
          className={`h-full ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
