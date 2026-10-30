import type { Alert } from "../types";

interface Props {
  alerts: Alert[];
  onRemove: (alertId: number) => void;
}

export default function CaseAlerts({ alerts, onRemove }: Props) {
  if (alerts.length === 0) return <p className="muted">No alerts in this case yet.</p>;
  return (
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Category</th>
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
            <td>{a.base_score}</td>
            <td>
              <button type="button" onClick={() => onRemove(a.id)}>Remove</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
