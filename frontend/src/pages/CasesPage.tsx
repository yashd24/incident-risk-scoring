import { useEffect, useState } from "react";
import { api } from "../api";
import type { CaseListItem } from "../types";

export default function CasesPage() {
  const [cases, setCases] = useState<CaseListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => api.listCases().then(setCases).catch((e: Error) => setError(e.message));
  useEffect(() => {
    load();
  }, []);

  const remove = async (c: CaseListItem) => {
    if (!window.confirm(`Delete case "${c.name}"? Its alerts and policies are removed from it.`)) return;
    setError(null);
    try {
      await api.deleteCase(c.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <section>
      <h2>All cases</h2>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      {cases === null ? (
        <p className="muted">Loading…</p>
      ) : cases.length === 0 ? (
        <p className="muted">
          No cases yet. <a href="#/new">Create one</a> to get started.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Alerts</th>
              <th>Score</th>
              <th>Severity</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {cases.map((c) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>
                  <a href={`#/cases/${c.id}`}>{c.name}</a>
                </td>
                <td>{c.alert_count}</td>
                <td>{c.final_score}</td>
                <td>
                  <span className={`badge ${c.severity.toLowerCase()}`}>{c.severity}</span>
                </td>
                <td>
                  <button onClick={() => remove(c)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
