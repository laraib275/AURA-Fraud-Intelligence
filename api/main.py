from fastapi import FastAPI, HTTPException

from src.investigation.ai_investigator import AIInvestigator
from src.investigation.investigation_engine import InvestigationEngine

app = FastAPI(
    title="AURA Fraud Intelligence API",
    description="Fraud detection and transaction investigation API",
    version="1.0.0",
)


# ---------------------------------------------------------
# LOAD ENGINES ONCE WHEN API STARTS
# ---------------------------------------------------------

engine = InvestigationEngine()
ai_investigator = AIInvestigator()


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "application": "AURA Fraud Intelligence",
        "status": "online",
        "service": "Fraud Investigation API",
    }


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ---------------------------------------------------------
# TRANSACTION INVESTIGATION
# ---------------------------------------------------------

@app.get("/investigate/{transaction_id}")
def investigate(transaction_id: str):

    report = engine.investigate_transaction(
        transaction_id
    )

    if "error" in report:

        raise HTTPException(
            status_code=404,
            detail=report["error"],
        )

    return report


# ---------------------------------------------------------
# AI INVESTIGATION REPORT
# ---------------------------------------------------------

@app.get("/investigate/{transaction_id}/ai-report")
def ai_investigation_report(transaction_id: str):

    # First obtain the normal AURA investigation
    investigation = engine.investigate_transaction(
        transaction_id
    )

    # Transaction not found / investigation error
    if "error" in investigation:

        raise HTTPException(
            status_code=404,
            detail=investigation["error"],
        )

    # Generate AI Investigator report
    report = ai_investigator.generate_report(
        investigation
    )

    return report