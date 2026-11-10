from datetime import date, datetime
from decimal import Decimal
from typing import Optional

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
from src.agents.action_router import ActionDecision, ActionType, AURAActionRouter
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


class CreateCaseRequest(BaseModel):
    transaction_id: str
    priority: Optional[str] = None
    analyst_notes: Optional[str] = ""
    assigned_analyst: Optional[str] = "AURA_AGENT"


class UpdateCaseRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    analyst_notes: Optional[str] = None
    assigned_analyst: Optional[str] = None


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
# CEO SUMMARY DIRECT ENDPOINT
# ============================================================

@app.get("/investigate/{transaction_id}/ceo-summary")
def get_ceo_summary(
    transaction_id: str
):
    transaction_id = transaction_id.strip()
    if not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID cannot be empty."
        )

    decision = ActionDecision(
        action=ActionType.GENERATE_CEO_SUMMARY,
        confidence=1.0,
        explicit_request=True,
        reason="Direct API request for CEO summary",
    )

    execution = action_executor.execute(
        decision=decision,
        transaction_id=transaction_id,
    )

    if not execution.success:
        raise HTTPException(
            status_code=400,
            detail=execution.message
        )

    return make_json_safe(execution.data)


# ============================================================
# VIDEO DOWNLOAD / STREAM ENDPOINT
# ============================================================

@app.get("/investigate/{transaction_id}/video")
def get_investigation_video(
    transaction_id: str
):
    from pathlib import Path

    transaction_id = transaction_id.strip()
    if not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID cannot be empty."
        )

    output_slug = f"aura_{str(transaction_id).replace('-', '_').replace(' ', '_')}"
    video_path = Path("data/video") / output_slug / f"{output_slug}.mp4"

    if not video_path.exists():
        decision = ActionDecision(
            action=ActionType.GENERATE_VIDEO,
            confidence=1.0,
            explicit_request=True,
            reason="Direct API request for video",
        )
        execution = action_executor.execute(
            decision=decision,
            transaction_id=transaction_id,
        )
        if not execution.success:
            raise HTTPException(
                status_code=500,
                detail=f"Video generation failed: {execution.message}"
            )
        action_data = execution.data or {}
        mp4_path_str = action_data.get("mp4_path")
        if not mp4_path_str or not Path(mp4_path_str).exists():
            raise HTTPException(
                status_code=404,
                detail="Video MP4 file is not available. Visual frame assets were generated in the output directory."
            )
        video_path = Path(mp4_path_str)

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"AURA_Investigation_{transaction_id}.mp4",
    )


# ============================================================
# CASE MANAGEMENT ENDPOINTS
# ============================================================

@app.post("/cases")
def create_case_endpoint(request: CreateCaseRequest):
    """Open or update a fraud investigation case."""
    txn_id = request.transaction_id.strip()
    if not txn_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID cannot be empty."
        )

    decision = ActionDecision(
        action=ActionType.CREATE_CASE,
        confidence=1.0,
        explicit_request=True,
        reason="Direct API request to create case",
    )

    execution = action_executor.execute(
        decision=decision,
        transaction_id=txn_id,
        question=request.analyst_notes,
    )

    if not execution.success:
        raise HTTPException(
            status_code=400,
            detail=execution.message
        )

    case_data = execution.data or {}
    case_id = case_data.get("case_id")
    if case_id and (request.priority or request.assigned_analyst):
        updated = action_executor.case_store.update_case(
            case_id=case_id,
            priority=request.priority,
            assigned_analyst=request.assigned_analyst,
        )
        if updated:
            case_data = updated

    return make_json_safe(case_data)


@app.get("/cases")
def list_cases_endpoint(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """List investigation cases with optional status or priority filters."""
    cases = action_executor.case_store.list_cases(
        status=status,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    return {
        "count": len(cases),
        "limit": limit,
        "offset": offset,
        "cases": make_json_safe(cases),
    }


@app.get("/cases/stats/summary")
def get_case_statistics():
    """Retrieve case overview metrics and status breakdown."""
    stats = action_executor.case_store.get_statistics()
    return make_json_safe(stats)


@app.get("/cases/{case_id}")
def get_case_endpoint(case_id: str):
    """Retrieve full case details along with chronological audit log."""
    case = action_executor.case_store.get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"Case {case_id} not found."
        )

    logs = action_executor.case_store.get_audit_logs(case_id)

    return {
        "case": make_json_safe(case),
        "audit_logs": make_json_safe(logs),
    }


@app.patch("/cases/{case_id}")
def update_case_endpoint(case_id: str, request: UpdateCaseRequest):
    """Update case status, priority, or analyst notes."""
    existing = action_executor.case_store.get_case(case_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Case {case_id} not found."
        )

    updated = action_executor.case_store.update_case(
        case_id=case_id,
        status=request.status,
        priority=request.priority,
        analyst_notes=request.analyst_notes,
        assigned_analyst=request.assigned_analyst,
    )
    return make_json_safe(updated)


@app.get("/cases/by-transaction/{transaction_id}")
def get_case_by_transaction_endpoint(transaction_id: str):
    """Find case associated with a transaction."""
    case = action_executor.case_store.get_case_by_transaction(transaction_id)
    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"No case found for transaction {transaction_id}."
        )
    return make_json_safe(case)


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

    # ANALYZE_TRANSACTIONS and CREATE_CASE handle their own failure
    # responses below — do not raise 400 for them here.
    _hard_fail_actions = {
        ActionType.ANSWER_QUESTION,
        ActionType.GENERATE_PDF,
        ActionType.GENERATE_VIDEO,
        ActionType.GENERATE_CEO_SUMMARY,
    }

    if not execution.success and decision.action in _hard_fail_actions:

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

        action_data = execution.data or {}
        mp4_path = action_data.get("mp4_path")

        return {
            "transaction_id": transaction_id,
            "question": question,
            "action": decision.action.value,
            "explicit_request": decision.explicit_request,
            "confidence": decision.confidence,
            "message": execution.message,
            "video": {
                "available": bool(mp4_path),
                "download_endpoint": (
                    f"/investigate/{transaction_id}/video"
                    if mp4_path else None
                ),
                "title": action_data.get("video_title"),
                "duration_seconds": action_data.get("duration_seconds"),
                "total_scenes": action_data.get("total_scenes"),
                "output_directory": action_data.get("output_directory"),
            },
            "action_result": make_json_safe(
                action_data
            ),
        }

    # ========================================================
    # 5. CEO SUMMARY
    # ========================================================

    if decision.action == ActionType.GENERATE_CEO_SUMMARY:

        action_data = execution.data or {}

        return {
            "transaction_id": transaction_id,
            "question": question,
            "action": decision.action.value,
            "explicit_request": decision.explicit_request,
            "confidence": decision.confidence,
            "message": execution.message,
            "executive_summary": action_data.get("executive_summary", ""),
            "risk_level": action_data.get("risk_level"),
            "risk_score": action_data.get("risk_score"),
            "action_result": make_json_safe(
                action_data
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

        action_data = execution.data or {}

        return {
            "transaction_id": transaction_id,
            "question": question,
            "action": decision.action.value,
            "explicit_request": decision.explicit_request,
            "confidence": decision.confidence,
            "message": execution.message,
            "case": make_json_safe(action_data),
            "action_result": make_json_safe(action_data),
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