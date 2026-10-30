from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class PolicyName(str, Enum):
    REPEAT_NOISE_DAMPING = "REPEAT_NOISE_DAMPING"
    CRITICAL_ASSET_BOOST = "CRITICAL_ASSET_BOOST"
    APT_CAMPAIGN_LINK = "APT_CAMPAIGN_LINK"


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    source_host: str
    base_score: int


class CaseName(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class Selection(BaseModel):
    alert_ids: list[int] = []
    policies: list[PolicyName] = []


class CaseCreate(CaseName, Selection):
    pass


class CaseUpdate(Selection):
    alert_ids: list[int]
    policies: list[PolicyName]


class PreviewIn(Selection):
    pass


class CaseListItem(BaseModel):
    id: int
    name: str
    alert_count: int
    final_score: int
    severity: str


class CaseDetail(BaseModel):
    id: int
    name: str
    created_at: datetime
    alerts: list[AlertOut]
    policies: list[PolicyName]


class AddAlert(BaseModel):
    alert_id: int


class PoliciesIn(BaseModel):
    policies: list[PolicyName]


class AdjustmentOut(BaseModel):
    policy: PolicyName
    applied: bool
    points: int
    detail: str


class SummaryOut(BaseModel):
    raw_score: int
    adjustments: list[AdjustmentOut]
    final_score: int
    severity: str
