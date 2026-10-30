export type PolicyName =
  | "REPEAT_NOISE_DAMPING"
  | "CRITICAL_ASSET_BOOST"
  | "APT_CAMPAIGN_LINK";

export type Severity = "Low" | "Medium" | "High" | "Critical";

export interface Alert {
  id: number;
  title: string;
  category: string;
  source_host: string;
  base_score: number;
}

export interface CaseListItem {
  id: number;
  name: string;
  alert_count: number;
  final_score: number;
  severity: Severity;
}

export interface CaseDetail {
  id: number;
  name: string;
  created_at: string;
  alerts: Alert[];
  policies: PolicyName[];
}

export interface Adjustment {
  policy: PolicyName;
  applied: boolean;
  points: number;
  detail: string;
}

export interface Summary {
  raw_score: number;
  adjustments: Adjustment[];
  final_score: number;
  severity: Severity;
}
