import { useEffect, useState } from "react";
import { api } from "../api";
import type { Alert, PolicyName, Summary } from "../types";
import AlertsTable from "../components/AlertsTable";
import CaseAlerts from "../components/CaseAlerts";
import PolicyPanel from "../components/PolicyPanel";
import SummaryPanel from "../components/SummaryPanel";

export default function NewCasePage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [name, setName] = useState("");
  const [selected, setSelected] = useState<Alert[]>([]);
  const [policies, setPolicies] = useState<PolicyName[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.listAlerts().then(setAlerts).catch((e: Error) => setError(e.message));
  }, []);

  // Live preview of the unsaved selection, scored by the server.
  useEffect(() => {
    let stale = false;
    api
      .previewSummary(selected.map((a) => a.id), policies)
      .then((s) => !stale && setSummary(s))
      .catch((e: Error) => !stale && setError(e.message));
    return () => {
      stale = true;
    };
  }, [selected, policies]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const c = await api.createCase(name, selected.map((a) => a.id), policies);
      window.location.hash = `#/cases/${c.id}`;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSaving(false);
    }
  };

  const add = (id: number) => {
    const a = alerts.find((x) => x.id === id);
    if (a) setSelected((cur) => (cur.some((x) => x.id === id) ? cur : [...cur, a]));
  };
  const remove = (id: number) => setSelected((cur) => cur.filter((x) => x.id !== id));

  return (
    <form onSubmit={submit}>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      <div className="columns">
        <section>
          <h2>Available alerts</h2>
          <AlertsTable
            alerts={alerts}
            caseAlertIds={new Set(selected.map((a) => a.id))}
            onAdd={add}
          />
        </section>
        <section>
          <h2>Alerts in this case</h2>
          <CaseAlerts alerts={selected} onRemove={remove} />
          <PolicyPanel policies={policies} onChange={setPolicies} />
          {summary && (
            <SummaryPanel summary={summary}>
              <hr />
              <label>
                Case name <span className="req">*</span>
                <input
                  value={name}
                  required
                  maxLength={100}
                  placeholder="e.g. Finance phishing wave"
                  onChange={(e) => {
                    setName(e.target.value);
                    e.target.setCustomValidity(e.target.value.trim() ? "" : "Case name is required");
                  }}
                />
              </label>
              <button type="submit" disabled={saving || selected.length === 0}>
                {saving ? "Creating..." : "Create case"}
              </button>
              {selected.length === 0 && <p className="muted small hint">Add at least one alert to create a case.</p>}
            </SummaryPanel>
          )}
        </section>
      </div>
    </form>
  );
}
