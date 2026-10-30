from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (CheckConstraint("base_score BETWEEN 1 AND 40", name="ck_alerts_base_score"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    source_host: Mapped[str] = mapped_column(String, nullable=False)
    base_score: Mapped[int] = mapped_column(nullable=False)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    case_alerts: Mapped[list["CaseAlert"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="CaseAlert.alert_id"
    )
    case_policies: Mapped[list["CasePolicy"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="CasePolicy.policy_name"
    )


class CaseAlert(Base):
    __tablename__ = "case_alerts"

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True
    )
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    case: Mapped[Case] = relationship(back_populates="case_alerts")
    alert: Mapped[Alert] = relationship()


class CasePolicy(Base):
    __tablename__ = "case_policies"

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True
    )
    policy_name: Mapped[str] = mapped_column(String, primary_key=True)

    case: Mapped[Case] = relationship(back_populates="case_policies")
