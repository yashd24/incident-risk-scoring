import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Alert, CaseDetail, PolicyName, Summary } from "../types";
import AlertsTable from "../components/AlertsTable";
import CaseAlerts from "../components/CaseAlerts";
import PolicyPanel from "../components/PolicyPanel";
import SummaryPanel from "../components/SummaryPanel";

const sameSet = <T,>(a: T[], b: T[]) => a.length === b.length && a.every((x) => b.includes(x));

export default function CaseDetailPage({ id }: { id: number }) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [draftAlerts, setDraftAlerts] = useState<Alert[]>([]);
  const [draftPolicies, setDraftPolicies] = useState<PolicyName[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [text, setText] = useState("");

  const adopt = (d: CaseDetail) => {
    setDetail(d);
    setDraftAlerts(d.alerts);
    setDraftPolicies(d.policies);
  };

  const run = useCallback(async (fn: () => Promise<void>): Promise<boolean> => {
    setError(null);
    try {
      await fn();
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      return false;
    }
  }, []);

  useEffect(() => {
    run(async () => {
      const [a, d] = await Promise.all([api.listAlerts(), api.getCase(id)]);
      setAlerts(a);
      adopt(d);
    });
  }, [run, id]);

  // Live preview of the unsaved draft, scored by the server.
  useEffect(() => {
    if (!detail) return;
    let stale = false;
    api
      .previewSummary(draftAlerts.map((a) => a.id), draftPolicies)
      .then((s) => !stale && setSummary(s))
      .catch((e: Error) => !stale && setError(e.message));
    return () => {
      stale = true;
    };
  }, [detail, draftAlerts, draftPolicies]);

  const dirty =
    detail !== null &&
    (!sameSet(draftAlerts.map((a) => a.id), detail.alerts.map((a) => a.id)) ||
      !sameSet(draftPolicies, detail.policies));

  const edit = (fn: () => void) => {
    setSaved(false);
    fn();
  };

  const update = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const ok = await run(async () => {
      adopt(await api.updateCase(id, draftAlerts.map((a) => a.id), draftPolicies));
    });
    setSaved(ok);
    setSaving(false);
  };

  const rename = async (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim() === detail?.name) {
      setRenaming(false); // unchanged: nothing to save
      return;
    }
    const ok = await run(async () => {
      const d = await api.renameCase(id, text);
      setDetail((cur) => (cur ? { ...cur, name: d.name } : cur));
    });
    if (ok) setRenaming(false);
  };

  const remove = () => {
    if (!detail) return;
    if (!window.confirm(`Delete case "${detail.name}"? Its alerts and policies are removed from it.`)) return;
    run(async () => {
      await api.deleteCase(id);
      window.location.hash = "#/cases";
    });
  };

  if (!detail) {
    return error ? (
      <div className="error" role="alert">
        {error} <a href="#/cases">Back to all cases</a>
      </div>
    ) : (
      <p className="muted">Loading...</p>
    );
  }

  const add = (aid: number) => {
    const a = alerts.find((x) => x.id === aid);
    if (a) edit(() => setDraftAlerts((cur) => (cur.some((x) => x.id === aid) ? cur : [...cur, a])));
  };

  return (
    <>
      <div className="bar case-header">
        {renaming ? (
          <form onSubmit={rename} className="inline">
            <input
              autoFocus
              required
              value={text}
              maxLength={100}
              aria-label="Case name"
              onChange={(e) => {
                setText(e.target.value);
                e.target.setCustomValidity(e.target.value.trim() ? "" : "Case name is required");
              }}
            />
            <button type="submit" aria-label="Save name" title="Save name">
              ✓
            </button>
            <button type="button" className="outline" aria-label="Cancel" title="Cancel" onClick={() => setRenaming(false)}>
              ✕
            </button>
          </form>
        ) : (
          <>
            <h2>{detail.name}</h2>
            <button
              className="outline"
              onClick={() => {
                setText(detail.name);
                setRenaming(true);
              }}
            >
              Rename
            </button>
            <button className="outline contrast" onClick={remove}>
              Delete
            </button>
          </>
        )}
      </div>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      <form onSubmit={update}>
        <div className="columns">
          <section>
            <h2>Available alerts</h2>
            <AlertsTable
              alerts={alerts}
              caseAlertIds={new Set(draftAlerts.map((a) => a.id))}
              hasCase
              onAdd={add}
            />
          </section>
          <section>
            <h2>Alerts in this case</h2>
            <CaseAlerts
              alerts={draftAlerts}
              onRemove={(aid) => edit(() => setDraftAlerts((cur) => cur.filter((x) => x.id !== aid)))}
            />
            <PolicyPanel policies={draftPolicies} onChange={(p) => edit(() => setDraftPolicies(p))} />
            {summary && (
              <SummaryPanel summary={summary}>
                <hr />
                <button type="submit" disabled={!dirty || saving || draftAlerts.length === 0}>
                  {saving ? "Updating..." : "Update case"}
                </button>
                {draftAlerts.length === 0 && (
                  <p className="muted small hint">A case needs at least one alert.</p>
                )}
                {saved && !dirty && <p className="saved">Saved</p>}
              </SummaryPanel>
            )}
          </section>
        </div>
      </form>
    </>
  );
}
