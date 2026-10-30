import type { PolicyName } from "../types";

const DAMPING: PolicyName = "REPEAT_NOISE_DAMPING";
const ESCALATIONS: { value: PolicyName | null; label: string }[] = [
  { value: null, label: "None" },
  { value: "CRITICAL_ASSET_BOOST", label: "CRITICAL_ASSET_BOOST" },
  { value: "APT_CAMPAIGN_LINK", label: "APT_CAMPAIGN_LINK" },
];

interface Props {
  policies: PolicyName[];
  onChange: (policies: PolicyName[]) => void;
}

export default function PolicyPanel({ policies, onChange }: Props) {
  const damping = policies.includes(DAMPING);
  const escalation = policies.find((p) => p !== DAMPING) ?? null;

  const emit = (d: boolean, e: PolicyName | null) => {
    const next: PolicyName[] = [];
    if (d) next.push(DAMPING);
    if (e) next.push(e);
    onChange(next);
  };

  return (
    <fieldset>
      <legend>Policies</legend>
      <label className="row">
        <input type="checkbox" checked={damping} onChange={(ev) => emit(ev.target.checked, escalation)} />
        REPEAT_NOISE_DAMPING
      </label>
      <div className="muted small">Escalation (at most one)</div>
      {ESCALATIONS.map((o) => (
        <label className="row" key={o.label}>
          <input
            type="radio"
            name="escalation"
            checked={escalation === o.value}
            onChange={() => emit(damping, o.value)}
          />
          {o.label}
        </label>
      ))}
    </fieldset>
  );
}
