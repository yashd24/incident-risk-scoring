"""Insert the seed alerts if the alerts table is empty (safe to run on every start)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Alert

SEED_ALERTS = [
    ("Phishing email with credential-harvesting link", "phishing", "mail-gw-01", 18),
    ("Spear-phishing attachment to finance team", "phishing", "mail-gw-01", 32),
    ("Ransomware signature detected", "malware", "fin-db-02", 40),
    ("Suspicious PowerShell dropper", "malware", "hr-laptop-17", 27),
    ("Port scan from external IP", "network_scan", "fw-edge-01", 12),
    ("Internal subnet sweep", "network_scan", "dc-01", 22),
    ("Repeated SSH probe", "network_scan", "test-vm-03", 8),
    ("Brute-force login attempts", "credential_access", "vpn-gw-01", 25),
]


def seed(db: Session) -> bool:
    if db.scalar(select(func.count()).select_from(Alert)):
        return False
    for title, category, host, score in SEED_ALERTS:  # in order, so ids are 1..8
        db.add(Alert(title=title, category=category, source_host=host, base_score=score))
        db.flush()
    db.commit()
    return True


if __name__ == "__main__":
    with SessionLocal() as session:
        print("Seeded alerts" if seed(session) else "Alerts already present, skipping seed")
