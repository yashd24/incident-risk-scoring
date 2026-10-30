import type { Summary } from "../types";

export default function SummaryPanel({ summary, children }: { summary: Summary; children?: React.ReactNode }) {
  return (
    <article className="summary">
      <h3>Score summary</h3>
      <div className="line">
        <span>Raw score</span>
        <strong>{summary.raw_score}</strong>
      </div>
      {summary.adjustments.map((a) => (
        <div key={a.policy} className={`adj ${a.applied ? "" : "not-applied"}`}>
          <div className="line">
            <span>{a.policy}</span>
            <strong>{a.applied ? (a.points > 0 ? `+${a.points}` : a.points) : "not applied"}</strong>
          </div>
          <div className="muted small">{a.detail}</div>
        </div>
      ))}
      <div className="line total">
        <span>Final score</span>
        <strong>{summary.final_score}</strong>
      </div>
      <div className={`badge ${summary.severity.toLowerCase()}`}>{summary.severity}</div>
      {children}
    </article>
  );
}
