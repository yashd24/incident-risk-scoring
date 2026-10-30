import type { Alert } from "../types";

interface Props {
  alerts: Alert[];
  caseAlertIds: Set<number>;
  onAdd: (alertId: number) => void;
}

export default function AlertsTable({ alerts, caseAlertIds, onAdd }: Props) {
  return (
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Category</th>
          <th>Host</th>
          <th>Score</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {alerts.map((a) => (
          <tr key={a.id}>
            <td>{a.id}</td>
            <td>{a.title}</td>
            <td>{a.category}</td>
            <td>{a.source_host}</td>
            <td>{a.base_score}</td>
            <td>
              {caseAlertIds.has(a.id) ? (
                <span className="muted">Added</span>
              ) : (
                <button type="button" onClick={() => onAdd(a.id)}>
                  Add to case
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
