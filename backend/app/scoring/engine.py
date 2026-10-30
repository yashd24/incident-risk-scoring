"""Pure scoring engine. No database or web imports."""

from dataclasses import dataclass
from typing import Iterable

DAMPING = "REPEAT_NOISE_DAMPING"
BOOST = "CRITICAL_ASSET_BOOST"
APT = "APT_CAMPAIGN_LINK"
ESCALATIONS = (BOOST, APT)

BOOST_PERCENT = 20
BOOST_CAP = 30
APT_POINTS = 25
APT_THRESHOLD = 50
MAX_SCORE = 100


@dataclass(frozen=True)
class AlertInput:
    id: int
    category: str
    base_score: int


@dataclass(frozen=True)
class Adjustment:
    policy: str
    applied: bool
    points: int
    detail: str


@dataclass(frozen=True)
class Summary:
    raw_score: int
    adjustments: list[Adjustment]
    final_score: int
    severity: str


def severity_for(score: int) -> str:
    if score >= 85:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def _ids(alerts: Iterable[AlertInput]) -> str:
    return ", ".join(str(a.id) for a in alerts)


def _damping(alerts: list[AlertInput]) -> Adjustment:
    scans = sorted(
        (a for a in alerts if a.category == "network_scan"),
        key=lambda a: (a.base_score, a.id),
    )
    if len(scans) < 2:
        return Adjustment(DAMPING, False, 0, "No duplicate network_scan alerts to ignore")
    kept = scans[-1]  # highest score, ties broken by highest alert id
    ignored = sorted(scans[:-1], key=lambda a: a.id)
    points = -sum(a.base_score for a in ignored)
    if points == 0:
        return Adjustment(DAMPING, False, 0, "No duplicate network_scan alerts to ignore")
    detail = f"Kept alert {kept.id} ({kept.base_score}); ignored alerts {_ids(ignored)}"
    return Adjustment(DAMPING, True, points, detail)


def _boost(score: int) -> Adjustment:
    points = min(score * BOOST_PERCENT // 100, BOOST_CAP)
    if points == 0:
        return Adjustment(BOOST, False, 0, "No score to boost")
    detail = f"{BOOST_PERCENT}% of {score} = {points} (cap {BOOST_CAP})"
    return Adjustment(BOOST, True, points, detail)


def _apt(score: int) -> Adjustment:
    if score < APT_THRESHOLD:
        return Adjustment(APT, False, 0, f"Score {score} is below {APT_THRESHOLD}")
    return Adjustment(
        APT, True, APT_POINTS, f"Score {score} is at least {APT_THRESHOLD}: +{APT_POINTS}"
    )


def compute_summary(alerts: Iterable[AlertInput], policies: Iterable[str]) -> Summary:
    alerts = list(alerts)
    requested = set(policies)
    escalations = requested & set(ESCALATIONS)
    if len(escalations) > 1:
        raise ValueError("At most one escalation policy may be requested")

    raw = sum(a.base_score for a in alerts)
    score = raw
    adjustments: list[Adjustment] = []

    if DAMPING in requested:
        damping = _damping(alerts)
        adjustments.append(damping)
        score += damping.points  # not applied => 0 points

    escalation_points = 0
    if BOOST in requested:
        boost = _boost(score)
        adjustments.append(boost)
        escalation_points = boost.points
    elif APT in requested:
        apt = _apt(score)
        adjustments.append(apt)
        escalation_points = apt.points

    final = min(score + escalation_points, MAX_SCORE)
    return Summary(raw, adjustments, final, severity_for(final))
