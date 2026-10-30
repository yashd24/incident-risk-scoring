import type { Alert, CaseDetail, CaseListItem, PolicyName, Summary } from "./types";

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      const d = data.detail;
      if (typeof d === "string") message = d;
      else if (Array.isArray(d) && d.length) message = d.map((e: { msg: string }) => e.msg).join("; ");
    } catch {
      /* keep default message */
    }
    throw new Error(message);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  listAlerts: () => request<Alert[]>("GET", "/alerts"),
  listCases: () => request<CaseListItem[]>("GET", "/cases"),
  createCase: (name: string, alertIds: number[] = [], policies: PolicyName[] = []) =>
    request<CaseDetail>("POST", "/cases", { name, alert_ids: alertIds, policies }),
  previewSummary: (alertIds: number[], policies: PolicyName[]) =>
    request<Summary>("POST", "/summary/preview", { alert_ids: alertIds, policies }),
  renameCase: (id: number, name: string) => request<CaseDetail>("PATCH", `/cases/${id}`, { name }),
  updateCase: (id: number, alertIds: number[], policies: PolicyName[]) =>
    request<CaseDetail>("PUT", `/cases/${id}`, { alert_ids: alertIds, policies }),
  deleteCase: (id: number) => request<void>("DELETE", `/cases/${id}`),
  getCase: (id: number) => request<CaseDetail>("GET", `/cases/${id}`),
  addAlert: (id: number, alertId: number) =>
    request<CaseDetail>("POST", `/cases/${id}/alerts`, { alert_id: alertId }),
  removeAlert: (id: number, alertId: number) =>
    request<void>("DELETE", `/cases/${id}/alerts/${alertId}`),
  setPolicies: (id: number, policies: PolicyName[]) =>
    request<CaseDetail>("PUT", `/cases/${id}/policies`, { policies }),
  getSummary: (id: number) => request<Summary>("GET", `/cases/${id}/summary`),
};
