from datetime import date, datetime
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pandas as pd
except ImportError:
    pd = None

from src.pipeline.ai_investigation_pipeline import AIInvestigationPipeline

# ============================================================
# AURA FRAUD INTELLIGENCE API
# ============================================================

app = FastAPI(
    title="AURA Fraud Intelligence API",
    description=(
        "AI-powered fraud detection, transaction investigation, "
        "RAG-assisted analysis, and AI investigation copilot."
    ),
    version="2.1.2",
)

pipeline = AIInvestigationPipeline()


# ============================================================
# REQUEST MODELS
# ============================================================

class AskAURARequest(BaseModel):
    question: str


# ============================================================
# JSON SERIALIZATION / NORMALIZATION
# ============================================================

def make_json_safe(value):
    """
    Convert objects returned by the investigation pipeline into
    values that FastAPI can safely serialize as JSON.

    Handles:
        - sets / frozensets
        - dictionaries
        - lists / tuples
        - numpy values
        - pandas values
        - datetime/date
        - Decimal
        - objects exposing to_dict()
        - objects exposing item()/tolist()
    """

    # --------------------------------------------------------
    # None / primitive values
    # --------------------------------------------------------
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    # --------------------------------------------------------
    # Decimal
    # --------------------------------------------------------
    if isinstance(value, Decimal):
        return float(value)

    # --------------------------------------------------------
    # Date / datetime
    # --------------------------------------------------------
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    # --------------------------------------------------------
    # Pandas
    # --------------------------------------------------------
    if pd is not None:

        if value is pd.NA:
            return None

        if isinstance(value, pd.Timestamp):
            return value.isoformat()

        if isinstance(value, pd.Series):
            return [
                make_json_safe(item)
                for item in value.tolist()
            ]

        if isinstance(value, pd.DataFrame):
            return make_json_safe(value.to_dict(orient="records"))

    # --------------------------------------------------------
    # NumPy
    # --------------------------------------------------------
    if np is not None:

        if isinstance(value, np.ndarray):
            return make_json_safe(value.tolist())

        if isinstance(value, np.generic):
            return make_json_safe(value.item())

    # --------------------------------------------------------
    # Dictionaries
    # --------------------------------------------------------
    if isinstance(value, dict):
        return {
            str(key): make_json_safe(val)
            for key, val in value.items()
        }

    # --------------------------------------------------------
    # SETS
    #
    # This is important for your current 500 error.
    #
    # A value such as:
    #
    #     {"transaction_id"}
    #
    # is a Python set, not a JSON string.
    #
    # We convert sets to lists so FastAPI can serialize them.
    # --------------------------------------------------------
    if isinstance(value, (set, frozenset)):

        converted = [
            make_json_safe(item)
            for item in value
        ]

        # Keep deterministic ordering where possible.
        try:
            return sorted(
                converted,
                key=lambda x: str(x)
            )
        except Exception:
            return converted

    # --------------------------------------------------------
    # Lists / tuples
    # --------------------------------------------------------
    if isinstance(value, (list, tuple)):
        return [
            make_json_safe(item)
            for item in value
        ]

    # --------------------------------------------------------
    # Objects with to_dict()
    # --------------------------------------------------------
    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return make_json_safe(value.to_dict())
        except Exception:
            pass

    # --------------------------------------------------------
    # NumPy-like item()
    # --------------------------------------------------------
    if hasattr(value, "item") and callable(value.item):
        try:
            return make_json_safe(value.item())
        except Exception:
            pass

    # --------------------------------------------------------
    # NumPy-like tolist()
    # --------------------------------------------------------
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return make_json_safe(value.tolist())
        except Exception:
            pass

    # --------------------------------------------------------
    # Final fallback
    # --------------------------------------------------------
    return str(value)


# ============================================================
# INVESTIGATION HELPERS
# ============================================================

def get_investigation(transaction_id: str):
    """
    Run the existing AURA investigation pipeline and extract
    the deterministic investigation object.

    We intentionally do NOT change the investigation logic here.
    This function only validates and normalizes its response.
    """

    transaction_id = transaction_id.strip()

    if not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID cannot be empty."
        )

    try:
        result = pipeline.investigate(transaction_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Investigation failed: {exc}"
        )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Investigation returned no result."
        )

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=404,
            detail=str(result["error"])
        )

    if not isinstance(result, dict):
        raise HTTPException(
            status_code=500,
            detail="Investigation pipeline returned an invalid response."
        )

    investigation = result.get("investigation")

    if investigation is None:
        raise HTTPException(
            status_code=500,
            detail="Investigation payload is missing."
        )

    return make_json_safe(investigation)


def get_ai_report(transaction_id: str):
    """
    Get the AI report from the existing pipeline while keeping
    the deterministic investigation flow unchanged.
    """

    transaction_id = transaction_id.strip()

    try:
        result = pipeline.investigate(transaction_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI investigation failed: {exc}"
        )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Investigation returned no result."
        )

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=404,
            detail=str(result["error"])
        )

    return make_json_safe(
        result.get("ai_report", {})
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "application": "AURA Fraud Intelligence",
        "status": "online",
        "service": "AI Fraud Investigation API",
        "version": "2.1.2",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "ai_pipeline": "ready",
    }


# ============================================================
# TRANSACTION INVESTIGATION
# ============================================================

@app.get("/investigate/{transaction_id}")
def investigate(transaction_id: str):

    investigation = get_investigation(transaction_id)

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # The dashboard expects the deterministic investigation
    # fields at the TOP LEVEL.
    #
    # Do not return the complete pipeline wrapper.
    # --------------------------------------------------------

    return investigation


# ============================================================
# AI INVESTIGATION REPORT
# ============================================================

@app.get("/investigate/{transaction_id}/ai-report")
def ai_investigation_report(transaction_id: str):

    transaction_id = transaction_id.strip()

    ai_report = get_ai_report(transaction_id)

    return {
        "transaction_id": transaction_id,
        "ai_report": ai_report,
    }


# ============================================================
# ASK AURA
# ============================================================

@app.post("/investigate/{transaction_id}/ask")
def ask_aura(
    transaction_id: str,
    request: AskAURARequest
):

    transaction_id = transaction_id.strip()
    question = request.question.strip()

    if not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID cannot be empty."
        )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # --------------------------------------------------------
    # Use the same deterministic investigation engine used by
    # the investigation workflow.
    # --------------------------------------------------------

    try:
        investigation = (
            pipeline.investigation_engine
            .investigate_transaction(transaction_id)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Investigation failed: {exc}"
        )

    if not investigation:
        raise HTTPException(
            status_code=404,
            detail="Investigation returned no result."
        )

    if isinstance(investigation, dict) and "error" in investigation:
        raise HTTPException(
            status_code=404,
            detail=str(investigation["error"])
        )

    # Normalize before sending it into the AI context.
    investigation = make_json_safe(investigation)

    # --------------------------------------------------------
    # RAG CONTEXT
    # --------------------------------------------------------

    try:
        rag_context = pipeline.rag.build_context(
            investigation,
            top_k=5
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"RAG context generation failed: {exc}"
        )

    rag_context = make_json_safe(rag_context)

    # --------------------------------------------------------
    # AURA SYSTEM PROMPT
    # --------------------------------------------------------

    system_prompt = """
You are AURA AI Copilot, an evidence-grounded fraud investigation assistant.

Your job is to help a fraud analyst understand the CURRENT TRANSACTION.

Use ONLY:
1. The supplied transaction investigation.
2. The retrieved fraud knowledge.

Never invent:
- transaction information
- customer information
- merchant information
- device information
- location information
- financial information
- behavioural information
- fraud information

Clearly distinguish:
- observed evidence
- model/rule outputs
- interpretation

Do not call a transaction fraudulent unless the supplied evidence supports
that conclusion.

When the transaction has a risk score or risk level, use the supplied
risk score and risk level exactly.

If evidence is unavailable, explicitly say that it is unavailable.

Answer professionally, concisely, and directly.
"""

    # --------------------------------------------------------
    # USER PROMPT
    # --------------------------------------------------------

    user_prompt = f"""
CURRENT TRANSACTION
Transaction ID: {transaction_id}

INVESTIGATION EVIDENCE
{investigation}

RETRIEVED FRAUD KNOWLEDGE
{rag_context}

ANALYST QUESTION
{question}

Answer the analyst's question using only the supplied evidence and
retrieved knowledge.

If the evidence does not answer the question, say so clearly.

Do not manufacture missing information.
"""

    # --------------------------------------------------------
    # LLM
    # --------------------------------------------------------

    try:
        answer = pipeline.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AURA AI generation failed: {exc}"
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "transaction_id": transaction_id,
        "question": question,
        "answer": make_json_safe(answer),
    }