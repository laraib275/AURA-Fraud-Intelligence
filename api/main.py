from datetime import date, datetime
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pandas as pd
except ImportError:
    pd = None

from src.agents.action_executor import AURAActionExecutor
from src.agents.action_router import ActionType, AURAActionRouter
from src.pipeline.ai_investigation_pipeline import AIInvestigationPipeline
from src.reporting.pdf_report import PDFReportGenerator

# ============================================================
# AURA FRAUD INTELLIGENCE API
# ============================================================

app = FastAPI(
    title="AURA Fraud Intelligence API",
    description=(
        "AI-powered fraud detection, transaction investigation, "
        "RAG-assisted analysis, AI investigation copilot, "
        "and natural-language action execution."
    ),
    version="2.3.0",
)


# ============================================================
# AURA CORE SERVICES
# ============================================================

pipeline = AIInvestigationPipeline()

action_router = AURAActionRouter()

action_executor = AURAActionExecutor(
    pipeline=pipeline
)


# ============================================================
# REQUEST MODELS
# ============================================================

class AskAURARequest(BaseModel):
    question: str


# ============================================================
# JSON SERIALIZATION / NORMALIZATION
# ============================================================

def make_json_safe(value):

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

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
            return make_json_safe(
                value.to_dict(orient="records")
            )

    if np is not None:

        if isinstance(value, np.ndarray):
            return make_json_safe(
                value.tolist()
            )

        if isinstance(value, np.generic):
            return make_json_safe(
                value.item()
            )

    if isinstance(value, dict):

        return {
            str(key): make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, (set, frozenset)):

        converted = [
            make_json_safe(item)
            for item in value
        ]

        try:
            return sorted(
                converted,
                key=lambda x: str(x)
            )
        except Exception:
            return converted

    if isinstance(value, (list, tuple)):

        return [
            make_json_safe(item)
            for item in value
        ]

    if hasattr(value, "to_dict") and callable(value.to_dict):

        try:
            return make_json_safe(
                value.to_dict()
            )
        except Exception:
            pass

    if hasattr(value, "item") and callable(value.item):

        try:
            return make_json_safe(
                value.item()
            )
        except Exception:
            pass

    if hasattr(value, "tolist") and callable(value.tolist):

        try:
            return make_json_safe(
                value.tolist()
            )
        except Exception:
            pass

    return str(value)


# ============================================================
# INVESTIGATION HELPERS
# ============================================================

def get_investigation(transaction_id: str):

    transaction_id = transaction_id.strip()

    if not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID cannot be empty."
        )

    try:
        result = pipeline.investigate(
            transaction_id
        )
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

    investigation = result.get(
        "investigation"
    )

    if investigation is None:
        raise HTTPException(
            status_code=500,
            detail="Investigation payload is missing."
        )

    return make_json_safe(
        investigation
    )


def get_pipeline_result(transaction_id: str):

    transaction_id = transaction_id.strip()

    if not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID cannot be empty."
        )

    try:
        result = pipeline.investigate(
            transaction_id
        )
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

    return result


def get_ai_report(transaction_id: str):

    result = get_pipeline_result(
        transaction_id
    )

    return make_json_safe(
        result.get(
            "ai_report",
            {}
        )
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
        "version": "2.3.0",
        "action_router": "ready",
        "action_executor": "ready",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "ai_pipeline": "ready",
        "action_router": "ready",
        "action_executor": "ready",
    }


# ============================================================
# TRANSACTION INVESTIGATION
# ============================================================

@app.get("/investigate/{transaction_id}")
def investigate(
    transaction_id: str
):

    return get_investigation(
        transaction_id
    )


# ============================================================
# AI INVESTIGATION REPORT
# ============================================================

@app.get("/investigate/{transaction_id}/ai-report")
def ai_investigation_report(
    transaction_id: str
):

    transaction_id = transaction_id.strip()

    return {
        "transaction_id": transaction_id,
        "ai_report": get_ai_report(
            transaction_id
        ),
    }


# ============================================================
# PDF GENERATION
# ============================================================

@app.get("/investigate/{transaction_id}/pdf")
def generate_investigation_pdf(
    transaction_id: str
):

    transaction_id = transaction_id.strip()

    if not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID cannot be empty."
        )

    try:

        pipeline_result = get_pipeline_result(
            transaction_id
        )

        generator = PDFReportGenerator()

        pdf_path = generator.generate(
            pipeline_result
        )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {exc}"
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"AURA_Investigation_{transaction_id}.pdf",
    )


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

    # ========================================================
    # 1. ACTION ROUTING
    # ========================================================

    decision = action_router.route(
        question
    )

    # ========================================================
    # 2. ACTION EXECUTION
    # ========================================================

    execution = action_executor.execute(
        decision=decision,
        transaction_id=transaction_id,
        question=question,
    )

    if not execution.success:

        raise HTTPException(
            status_code=400,
            detail=execution.message
        )

    # ========================================================
    # 3. EXPLICIT PDF REQUEST
    # ========================================================

    if decision.action == ActionType.GENERATE_PDF:

        try:

            pipeline_result = get_pipeline_result(
                transaction_id
            )

            generator = PDFReportGenerator()

            pdf_path = generator.generate(
                pipeline_result
            )

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=f"PDF generation failed: {exc}"
            )

        return {
            "transaction_id": transaction_id,
            "question": question,
            "action": decision.action.value,
            "explicit_request": decision.explicit_request,
            "confidence": decision.confidence,
            "message": "Investigation PDF generated successfully.",
            "action_result": make_json_safe(
                execution.data
            ),
            "pdf": {
                "available": True,
                "download_endpoint": (
                    f"/investigate/"
                    f"{transaction_id}/pdf"
                ),
                "filename": (
                    f"AURA_Investigation_"
                    f"{transaction_id}.pdf"
                ),
            },
        }

    # ========================================================
    # 4. VIDEO REQUEST
    # ========================================================

    if decision.action == ActionType.GENERATE_VIDEO:

        return {
            "transaction_id": transaction_id,
            "question": question,
            "action": decision.action.value,
            "explicit_request": decision.explicit_request,
            "confidence": decision.confidence,
            "message": (
                "Video generation request accepted. "
                "Video generation service will be connected "
                "in the next AURA action phase."
            ),
            "action_result": make_json_safe(
                execution.data
            ),
        }

    # ========================================================
    # 5. CEO SUMMARY
    # ========================================================

    if decision.action == ActionType.GENERATE_CEO_SUMMARY:

        return {
            "transaction_id": transaction_id,
            "question": question,
            "action": decision.action.value,
            "explicit_request": decision.explicit_request,
            "confidence": decision.confidence,
            "message": (
                "Executive intelligence request accepted."
            ),
            "action_result": make_json_safe(
                execution.data
            ),
        }

    # ========================================================
    # 6. MULTI-TRANSACTION ANALYSIS
    # ========================================================

    if decision.action == ActionType.ANALYZE_TRANSACTIONS:

        return {
            "transaction_id": transaction_id,
            "question": question,
            "action": decision.action.value,
            "explicit_request": decision.explicit_request,
            "confidence": decision.confidence,
            "message": (
                "Multi-transaction analysis request accepted."
            ),
            "action_result": make_json_safe(
                execution.data
            ),
        }

    # ========================================================
    # 7. CASE CREATION
    # ========================================================

    if decision.action == ActionType.CREATE_CASE:

        return {
            "transaction_id": transaction_id,
            "question": question,
            "action": decision.action.value,
            "explicit_request": decision.explicit_request,
            "confidence": decision.confidence,
            "message": (
                "Case creation request accepted. "
                "Case management will be connected "
                "in the case-management phase."
            ),
            "action_result": make_json_safe(
                execution.data
            ),
        }

    # ========================================================
    # 8. NORMAL AURA QUESTION
    # ========================================================

    try:

        investigation = (
            pipeline
            .investigation_engine
            .investigate_transaction(
                transaction_id
            )
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

    if (
        isinstance(investigation, dict)
        and "error" in investigation
    ):

        raise HTTPException(
            status_code=404,
            detail=str(
                investigation["error"]
            )
        )

    investigation = make_json_safe(
        investigation
    )

    # ========================================================
    # RAG
    # ========================================================

    try:

        rag_context = (
            pipeline
            .rag
            .build_context(
                investigation,
                top_k=5
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "RAG context generation failed: "
                f"{exc}"
            )
        )

    rag_context = make_json_safe(
        rag_context
    )

    # ========================================================
    # AURA SYSTEM PROMPT
    # ========================================================

    system_prompt = """
You are AURA AI Copilot, an evidence-grounded
fraud investigation assistant.

Your job is to help a fraud analyst understand
the CURRENT TRANSACTION.

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

Do not call a transaction fraudulent unless
the supplied evidence supports that conclusion.

When the transaction has a risk score or risk
level, use the supplied risk score and risk
level exactly.

If evidence is unavailable, explicitly say
that it is unavailable.

Answer professionally, concisely, and directly.
"""

    # ========================================================
    # USER PROMPT
    # ========================================================

    user_prompt = f"""
CURRENT TRANSACTION
Transaction ID: {transaction_id}

INVESTIGATION EVIDENCE
{investigation}

RETRIEVED FRAUD KNOWLEDGE
{rag_context}

ANALYST QUESTION
{question}

Answer the analyst's question using only the
supplied evidence and retrieved knowledge.

If the evidence does not answer the question,
say so clearly.

Do not manufacture missing information.
"""

    # ========================================================
    # LLM
    # ========================================================

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

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {
        "transaction_id": transaction_id,
        "question": question,
        "action": decision.action.value,
        "explicit_request": decision.explicit_request,
        "confidence": decision.confidence,
        "answer": make_json_safe(answer),
    }