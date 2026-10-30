import pytest

from app.scoring.engine import APT, BOOST, DAMPING, AlertInput, compute_summary, severity_for

# Seed alerts by id: (category, score)
SEED = {
    1: ("phishing", 18),
    2: ("phishing", 32),
    3: ("malware", 40),
    4: ("malware", 27),
    5: ("network_scan", 12),
    6: ("network_scan", 22),
    7: ("network_scan", 8),
    8: ("credential_access", 25),
}


def run(ids, policies=()):
    alerts = [AlertInput(i, SEED[i][0], SEED[i][1]) for i in ids]
    return compute_summary(alerts, policies)


@pytest.mark.parametrize(
    "ids,policies,final,severity",
    [
        ([3, 8], [APT], 90, "Critical"),
        ([1, 5, 6, 7], [DAMPING], 40, "Medium"),
        ([1, 5, 6, 7], [DAMPING, APT], 40, "Medium"),
        ([1, 5, 6, 7], [DAMPING, BOOST], 48, "Medium"),
        ([1, 6], [DAMPING], 40, "Medium"),
        ([1, 2], [APT], 75, "High"),
        ([4, 6], [APT], 49, "Medium"),
        ([2, 3, 4, 8], [BOOST], 100, "Critical"),
        ([2, 3, 4, 8], [APT], 100, "Critical"),
        ([], [BOOST], 0, "Low"),
    ],
)
def test_spec_examples(ids, policies, final, severity):
    s = run(ids, policies)
    assert s.final_score == final
    assert s.severity == severity


def test_no_policies():
    s = run([1, 2])
    assert (s.raw_score, s.final_score, s.adjustments) == (50, 50, [])


def test_damping_alone_details():
    s = run([1, 5, 6, 7], [DAMPING])
    (adj,) = s.adjustments
    assert (adj.applied, adj.points) == (True, -20)
    assert adj.detail == "Kept alert 6 (22); ignored alerts 5, 7"
    assert s.raw_score == 60


def test_damping_not_applied_reason():
    (adj,) = run([1, 6], [DAMPING]).adjustments
    assert not adj.applied and adj.points == 0
    assert adj.detail == "No duplicate network_scan alerts to ignore"


def test_boost_alone():
    s = run([1, 2], [BOOST])  # 50 -> +10
    (adj,) = s.adjustments
    assert (adj.applied, adj.points, s.final_score) == (True, 10, 60)
    assert adj.detail == "20% of 50 = 10 (cap 30)"


def test_boost_floors():
    s = run([6, 5], [BOOST])  # 34 -> 6.8 -> 6
    assert s.adjustments[0].points == 6
    assert s.final_score == 40


def test_boost_empty_case():
    (adj,) = run([], [BOOST]).adjustments
    assert not adj.applied and adj.detail == "No score to boost"


def test_boost_cap_displayed_points():
    alerts = [AlertInput(i, "malware", 40) for i in range(1, 5)]  # s = 160 -> 32 -> cap 30
    s = compute_summary(alerts, [BOOST])
    assert s.adjustments[0].points == 30
    assert s.final_score == 100


def test_damping_tie_uses_highest_id():
    alerts = [
        AlertInput(10, "network_scan", 15),
        AlertInput(12, "network_scan", 15),
        AlertInput(11, "network_scan", 15),
    ]
    s = compute_summary(alerts, [DAMPING])
    assert s.adjustments[0].detail == "Kept alert 12 (15); ignored alerts 10, 11"
    assert s.final_score == 15


def test_boost_and_apt_use_post_damping_score():
    # raw 60, damped 40: boost 8 (not 12); APT sees 40 not 60
    assert run([1, 5, 6, 7], [DAMPING, BOOST]).adjustments[1].points == 8
    assert not run([1, 5, 6, 7], [DAMPING, APT]).adjustments[1].applied


@pytest.mark.parametrize("target,applied,final", [(49, False, 49), (50, True, 75), (51, True, 76)])
def test_apt_threshold(target, applied, final):
    s = compute_summary([AlertInput(1, "phishing", target)], [APT])
    assert s.adjustments[0].applied is applied
    assert s.final_score == final


def test_apt_not_applied_reason():
    (adj,) = run([4, 6], [APT]).adjustments
    assert adj.detail == "Score 49 is below 50"


def test_adjustment_order_damping_then_escalation():
    s = run([1, 5, 6, 7], [APT, DAMPING])
    assert [a.policy for a in s.adjustments] == [DAMPING, APT]


def test_only_requested_policies_listed():
    assert [a.policy for a in run([1, 2], [APT]).adjustments] == [APT]


def test_cap_at_100():
    assert run([2, 3, 4, 8], [APT]).final_score == 100


def test_two_escalations_rejected():
    with pytest.raises(ValueError):
        run([1], [BOOST, APT])


@pytest.mark.parametrize(
    "score,sev",
    [(0, "Low"), (29, "Low"), (30, "Medium"), (59, "Medium"), (60, "High"),
     (84, "High"), (85, "Critical"), (100, "Critical")],
)
def test_severity_boundaries(score, sev):
    assert severity_for(score) == sev
