from fastapi import FastAPI, HTTPException

from src.investigation.investigation_engine import InvestigationEngine


app = FastAPI(
    title="AURA Fraud Intelligence API",
    description="Fraud detection and transaction investigation API",
    version="1.0.0",
)

# Load the investigation engine once when the API starts
engine = InvestigationEngine()


@app.get("/")
def root():
    return {
        "application": "AURA Fraud Intelligence",
        "status": "online",
        "service": "Fraud Investigation API",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


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