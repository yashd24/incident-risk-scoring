from fastapi import FastAPI

from app.routers import alerts, cases

app = FastAPI(title="Case Risk Scoring Tool")
app.include_router(alerts.router, prefix="/api")
app.include_router(cases.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
