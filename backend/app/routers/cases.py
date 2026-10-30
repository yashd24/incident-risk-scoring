from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Alert, Case, CaseAlert, CasePolicy
from app.schemas import (
    AddAlert,
    CaseCreate,
    CaseDetail,
    CaseUpdate,
    CaseListItem,
    CaseName,
    PoliciesIn,
    PreviewIn,
    SummaryOut,
)
from app.scoring.engine import ESCALATIONS, AlertInput, compute_summary

router = APIRouter()

NEEDS_ALERT = "A case needs at least one alert"
WITH_LINKS = (
    selectinload(Case.case_alerts).selectinload(CaseAlert.alert),
    selectinload(Case.case_policies),
)


def _load_case(db: Session, case_id: int) -> Case:
    case = db.scalars(select(Case).where(Case.id == case_id).options(*WITH_LINKS)).first()
    if case is None:
        raise HTTPException(404, "Case not found")
    return case


def _score(case: Case):
    alerts = [
        AlertInput(ca.alert.id, ca.alert.category, ca.alert.base_score)
        for ca in case.case_alerts
    ]
    return compute_summary(alerts, [p.policy_name for p in case.case_policies])


def _detail(case: Case) -> CaseDetail:
    return CaseDetail(
        id=case.id,
        name=case.name,
        created_at=case.created_at,
        alerts=[ca.alert for ca in case.case_alerts],
        policies=[p.policy_name for p in case.case_policies],
    )


@router.get("/cases", response_model=list[CaseListItem])
def list_cases(db: Session = Depends(get_db)):
    cases = db.scalars(select(Case).order_by(Case.id).options(*WITH_LINKS)).all()
    items = []
    for c in cases:
        s = _score(c)
        items.append(
            CaseListItem(
                id=c.id,
                name=c.name,
                alert_count=len(c.case_alerts),
                final_score=s.final_score,
                severity=s.severity,
            )
        )
    return items


def _checked_policies(policies) -> list[str]:
    names = {p.value for p in policies}
    if len(names & set(ESCALATIONS)) > 1:
        raise HTTPException(400, "Only one escalation policy may be selected")
    return sorted(names)


def _checked_alerts(db: Session, alert_ids: list[int]) -> list[Alert]:
    ids = list(dict.fromkeys(alert_ids))
    found = {a.id: a for a in db.scalars(select(Alert).where(Alert.id.in_(ids)))} if ids else {}
    missing = [i for i in ids if i not in found]
    if missing:
        raise HTTPException(404, f"Alert not found: {', '.join(map(str, missing))}")
    return [found[i] for i in ids]


@router.post("/cases", response_model=CaseDetail, status_code=201)
def create_case(body: CaseCreate, db: Session = Depends(get_db)):
    names = _checked_policies(body.policies)
    alerts = _checked_alerts(db, body.alert_ids)
    if not alerts:
        raise HTTPException(422, NEEDS_ALERT)
    case = Case(name=body.name)
    case.case_alerts = [CaseAlert(alert_id=a.id) for a in alerts]
    case.case_policies = [CasePolicy(policy_name=n) for n in names]
    db.add(case)
    db.commit()
    return _detail(_load_case(db, case.id))


@router.post("/summary/preview", response_model=SummaryOut)
def preview_summary(body: PreviewIn, db: Session = Depends(get_db)):
    """Score an unsaved selection of alerts and policies."""
    names = _checked_policies(body.policies)
    alerts = _checked_alerts(db, body.alert_ids)
    return compute_summary([AlertInput(a.id, a.category, a.base_score) for a in alerts], names)


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case(case_id: int, db: Session = Depends(get_db)):
    return _detail(_load_case(db, case_id))


@router.patch("/cases/{case_id}", response_model=CaseDetail)
def rename_case(case_id: int, body: CaseName, db: Session = Depends(get_db)):
    case = _load_case(db, case_id)
    case.name = body.name
    db.commit()
    return _detail(case)


@router.put("/cases/{case_id}", response_model=CaseDetail)
def update_case(case_id: int, body: CaseUpdate, db: Session = Depends(get_db)):
    """Replace the case's alerts and requested policies in one atomic call."""
    case = _load_case(db, case_id)
    names = _checked_policies(body.policies)
    alerts = _checked_alerts(db, body.alert_ids)
    if not alerts:
        raise HTTPException(422, NEEDS_ALERT)
    wanted = {a.id for a in alerts}
    for link in list(case.case_alerts):
        if link.alert_id not in wanted:
            case.case_alerts.remove(link)
    have = {ca.alert_id for ca in case.case_alerts}
    case.case_alerts.extend(CaseAlert(alert_id=i) for i in wanted - have)
    for p in list(case.case_policies):
        if p.policy_name not in names:
            case.case_policies.remove(p)
    have_p = {p.policy_name for p in case.case_policies}
    case.case_policies.extend(CasePolicy(policy_name=n) for n in names if n not in have_p)
    db.commit()
    db.expire_all()  # reload so the relationship order_by applies to the response
    return _detail(_load_case(db, case_id))


@router.delete("/cases/{case_id}", status_code=204)
def delete_case(case_id: int, db: Session = Depends(get_db)):
    case = _load_case(db, case_id)
    db.delete(case)
    db.commit()
    return Response(status_code=204)


@router.post("/cases/{case_id}/alerts", response_model=CaseDetail, status_code=201)
def add_alert(case_id: int, body: AddAlert, db: Session = Depends(get_db)):
    # db.get, not _load_case: loading the case's links into the session would make
    # SQLAlchemy reject the duplicate itself instead of the primary key doing it.
    if db.get(Case, case_id) is None:
        raise HTTPException(404, "Case not found")
    if db.get(Alert, body.alert_id) is None:
        raise HTTPException(404, "Alert not found")
    db.add(CaseAlert(case_id=case_id, alert_id=body.alert_id))
    try:
        db.commit()
    except IntegrityError:  # the (case_id, alert_id) primary key already exists
        db.rollback()
        raise HTTPException(409, f"Alert {body.alert_id} is already in this case")
    return _detail(_load_case(db, case_id))


@router.delete("/cases/{case_id}/alerts/{alert_id}", status_code=204)
def remove_alert(case_id: int, alert_id: int, db: Session = Depends(get_db)):
    case = _load_case(db, case_id)
    link = next((ca for ca in case.case_alerts if ca.alert_id == alert_id), None)
    if link is None:
        raise HTTPException(404, "Alert is not in this case")
    if len(case.case_alerts) == 1:
        raise HTTPException(422, NEEDS_ALERT)
    db.delete(link)
    db.commit()
    return Response(status_code=204)


@router.put("/cases/{case_id}/policies", response_model=CaseDetail)
def set_policies(case_id: int, body: PoliciesIn, db: Session = Depends(get_db)):
    case = _load_case(db, case_id)
    names = _checked_policies(body.policies)
    case.case_policies = [CasePolicy(policy_name=n) for n in names]
    db.commit()
    return _detail(_load_case(db, case_id))


@router.get("/cases/{case_id}/summary", response_model=SummaryOut)
def get_summary(case_id: int, db: Session = Depends(get_db)):
    return _score(_load_case(db, case_id))
