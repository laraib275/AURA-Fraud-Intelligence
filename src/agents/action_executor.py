from dataclasses import dataclass
from typing import Any, Dict, Optional

from database.case_store import CaseStore
from src.agents.action_router import ActionType, ActionDecision


@dataclass
class ActionResult:
    """
    Standard response returned after an AURA action is executed.
    """

    success: bool
    action: str
    message: str
    data: Optional[Dict[str, Any]] = None


class AURAActionExecutor:
    """
    Executes actions selected by AURAActionRouter.

    The executor is intentionally separated from the router:

        User Request
              ↓
        Action Router
              ↓
        Action Decision
              ↓
        Action Executor
              ↓
        Actual Tool / Service
    """

    def __init__(self, pipeline=None, case_store: Optional[CaseStore] = None):
        self.pipeline = pipeline
        self.case_store = case_store or CaseStore()

    def execute(
        self,
        decision: ActionDecision,
        transaction_id: Optional[str] = None,
        question: Optional[str] = None,
        transaction_ids: Optional[list] = None,
    ) -> ActionResult:

        action = decision.action

        # ---------------------------------------------------------
        # 1. NORMAL QUESTION
        # ---------------------------------------------------------
        if action == ActionType.ANSWER_QUESTION:
            return self._answer_question(
                transaction_id=transaction_id,
                question=question,
            )

        # ---------------------------------------------------------
        # 2. GENERATE PDF
        # ---------------------------------------------------------
        if action == ActionType.GENERATE_PDF:
            return self._generate_pdf(
                transaction_id=transaction_id,
            )

        # ---------------------------------------------------------
        # 3. GENERATE VIDEO
        # ---------------------------------------------------------
        if action == ActionType.GENERATE_VIDEO:
            return self._generate_video(
                transaction_id=transaction_id,
                question=question,
            )

        # ---------------------------------------------------------
        # 4. CEO EXECUTIVE SUMMARY
        # ---------------------------------------------------------
        if action == ActionType.GENERATE_CEO_SUMMARY:
            return self._generate_ceo_summary(
                transaction_id=transaction_id,
                question=question,
            )

        # ---------------------------------------------------------
        # 5. MULTI-TRANSACTION ANALYSIS
        # ---------------------------------------------------------
        if action == ActionType.ANALYZE_TRANSACTIONS:
            return self._analyze_transactions(
                transaction_ids=transaction_ids,
            )

        # ---------------------------------------------------------
        # 6. CREATE CASE
        # ---------------------------------------------------------
        if action == ActionType.CREATE_CASE:
            return self._create_case(
                transaction_id=transaction_id,
                question=question,
            )

        return ActionResult(
            success=False,
            action=str(action),
            message=f"Unsupported AURA action: {action}",
        )

    # =============================================================
    # ANSWER QUESTION
    # =============================================================

    def _answer_question(
        self,
        transaction_id: Optional[str],
        question: Optional[str],
    ) -> ActionResult:

        if not question:
            return ActionResult(
                success=False,
                action=ActionType.ANSWER_QUESTION.value,
                message="No question was provided.",
            )

        return ActionResult(
            success=True,
            action=ActionType.ANSWER_QUESTION.value,
            message="Question routed to AURA conversational intelligence.",
            data={
                "transaction_id": transaction_id,
                "question": question,
                "requires_ai_response": True,
            },
        )

    # =============================================================
    # GENERATE PDF
    # =============================================================

    def _generate_pdf(
        self,
        transaction_id: Optional[str],
    ) -> ActionResult:

        if not transaction_id:
            return ActionResult(
                success=False,
                action=ActionType.GENERATE_PDF.value,
                message="A transaction ID is required to generate the investigation PDF.",
            )

        return ActionResult(
            success=True,
            action=ActionType.GENERATE_PDF.value,
            message="PDF generation requested.",
            data={
                "transaction_id": transaction_id,
                "requires_pdf_generation": True,
            },
        )

    # =============================================================
    # =============================================================
    # GENERATE VIDEO
    # =============================================================

    def _generate_video(
        self,
        transaction_id: Optional[str],
        question: Optional[str] = None,
    ) -> ActionResult:

        if not transaction_id:
            return ActionResult(
                success=False,
                action=ActionType.GENERATE_VIDEO.value,
                message="A transaction ID is required to generate an investigation video.",
            )

        if not self.pipeline:
            return ActionResult(
                success=False,
                action=ActionType.GENERATE_VIDEO.value,
                message="Investigation pipeline is not configured in ActionExecutor.",
            )

        try:
            from src.video.video_engine import VideoEngine
            from src.video.video_renderer import VideoRenderer

            pipeline_result = self.pipeline.investigate(transaction_id)
            if not pipeline_result or "error" in pipeline_result:
                return ActionResult(
                    success=False,
                    action=ActionType.GENERATE_VIDEO.value,
                    message=f"Investigation data not found for transaction {transaction_id}.",
                )

            video_engine = VideoEngine()
            request_text = (
                question
                or f"Generate complete visual fraud investigation video for transaction {transaction_id}"
            )

            plan_response = video_engine.create_video_plan(
                request=request_text,
                investigation_result=pipeline_result,
            )

            renderer = VideoRenderer(fps=15)
            output_slug = f"aura_{str(transaction_id).replace('-', '_').replace(' ', '_')}"
            rendered_data = renderer.render(
                plan_response.get("video_plan", {}),
                output_name=output_slug,
            )
            mp4_path = renderer.compile_mp4(rendered_data, output_name=output_slug)

            return ActionResult(
                success=True,
                action=ActionType.GENERATE_VIDEO.value,
                message="Investigation video plan and visual scene assets generated successfully.",
                data={
                    "transaction_id": transaction_id,
                    "request": request_text,
                    "video_title": rendered_data.get("video_title"),
                    "story_type": rendered_data.get("story_type"),
                    "duration_seconds": rendered_data.get("duration_seconds"),
                    "total_scenes": len(rendered_data.get("scenes", [])),
                    "output_directory": rendered_data.get("output_directory"),
                    "mp4_path": mp4_path,
                    "scenes": rendered_data.get("scenes"),
                    "video_plan": plan_response.get("video_plan"),
                },
            )
        except Exception as exc:
            return ActionResult(
                success=False,
                action=ActionType.GENERATE_VIDEO.value,
                message=f"Video generation failed: {exc}",
            )

    # =============================================================
    # CEO EXECUTIVE SUMMARY
    # =============================================================

    def _generate_ceo_summary(
        self,
        transaction_id: Optional[str],
        question: Optional[str] = None,
    ) -> ActionResult:

        if not transaction_id:
            return ActionResult(
                success=False,
                action=ActionType.GENERATE_CEO_SUMMARY.value,
                message="A transaction ID is required to generate the executive summary.",
            )

        if not self.pipeline:
            return ActionResult(
                success=False,
                action=ActionType.GENERATE_CEO_SUMMARY.value,
                message="Investigation pipeline is not configured in ActionExecutor.",
            )

        try:
            pipeline_result = self.pipeline.investigate(transaction_id)
            if not pipeline_result or "error" in pipeline_result:
                return ActionResult(
                    success=False,
                    action=ActionType.GENERATE_CEO_SUMMARY.value,
                    message=f"Investigation data not found for transaction {transaction_id}.",
                )

            investigation = pipeline_result.get("investigation", {})
            rag_context = pipeline_result.get("rag_context", "")

            system_prompt = """You are AURA Executive Intelligence, a strategic fraud & risk advisory engine for C-level leadership (CEO, CRO, General Counsel).
Synthesize the technical investigation into an authoritative, high-impact Executive Brief.

Structure your response strictly into these 4 sections:
1. EXECUTIVE VERDICT & RISK ASSESSMENT: Immediate bottom-line conclusion, risk level, and total financial capital exposure.
2. THREAT CLASSIFICATION & MODUS OPERANDI: Nature of the attack (e.g., account takeover, synthetic identity, velocity burst) and behavioral patterns.
3. REGULATORY & COMPLIANCE IMPLICATIONS: AML/KYC impact, reporting triggers (Suspicious Activity Report - SAR), and chargeback liability exposure.
4. STRATEGIC ACTION DIRECTIVES: 3 specific, immediate business directives (e.g., account quarantine, merchant network review, rule threshold updates).

Tone: High-signal, executive, strategic, evidence-grounded. Do not invent unverified facts."""

            user_prompt = f"""TRANSACTION REFERENCE: {transaction_id}

INVESTIGATION EVIDENCE:
{investigation}

FRAUD KNOWLEDGE & REGULATORY CONTEXT:
{rag_context}

EXECUTIVE QUERY:
{question or 'Provide comprehensive C-suite executive briefing on this transaction'}

Deliver the executive brief now."""

            executive_summary = self.pipeline.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            risk_score = investigation.get("risk_score")
            risk_band = (
                investigation.get("risk_band")
                or investigation.get("risk_level")
                or "UNKNOWN"
            )
            amount = (
                investigation.get("amount")
                or investigation.get("amt")
                or (investigation.get("transaction") or {}).get("amt")
            )
            customer_id = (
                investigation.get("customer_id")
                or investigation.get("cc_num")
                or (investigation.get("transaction") or {}).get("cc_num")
            )

            return ActionResult(
                success=True,
                action=ActionType.GENERATE_CEO_SUMMARY.value,
                message="CEO Executive Intelligence Summary generated successfully.",
                data={
                    "transaction_id": transaction_id,
                    "executive_summary": executive_summary,
                    "risk_level": str(risk_band),
                    "risk_score": float(risk_score) if risk_score is not None else 0.0,
                    "amount": amount,
                    "customer_id": customer_id,
                },
            )
        except Exception as exc:
            return ActionResult(
                success=False,
                action=ActionType.GENERATE_CEO_SUMMARY.value,
                message=f"Executive summary generation failed: {exc}",
            )

    # =============================================================
    # MULTI-TRANSACTION ANALYSIS
    # =============================================================

    def _analyze_transactions(
        self,
        transaction_ids: Optional[list],
    ) -> ActionResult:

        if not transaction_ids:
            return ActionResult(
                success=False,
                action=ActionType.ANALYZE_TRANSACTIONS.value,
                message="No transaction IDs were provided.",
            )

        return ActionResult(
            success=True,
            action=ActionType.ANALYZE_TRANSACTIONS.value,
            message="Multi-transaction analysis requested.",
            data={
                "transaction_ids": transaction_ids,
                "transaction_count": len(transaction_ids),
                "requires_multi_transaction_analysis": True,
            },
        )

    # =============================================================
    # CREATE CASE
    # =============================================================

    def _create_case(
        self,
        transaction_id: Optional[str],
        question: Optional[str] = None,
    ) -> ActionResult:

        if not transaction_id:
            return ActionResult(
                success=False,
                action=ActionType.CREATE_CASE.value,
                message="A transaction ID is required to create a case.",
            )

        try:
            risk_score = 0.0
            risk_level = "UNKNOWN"

            if self.pipeline:
                try:
                    pipeline_result = self.pipeline.investigate(transaction_id)
                    if pipeline_result and "investigation" in pipeline_result:
                        inv = pipeline_result["investigation"]
                        risk_score = float(inv.get("risk_score") or 0.0)
                        risk_band = inv.get("risk_band") or inv.get("risk_level")
                        if risk_band:
                            risk_level = str(risk_band)
                except Exception:
                    pass

            notes = question or f"Investigation case opened for transaction {transaction_id}."
            case_record = self.case_store.create_case(
                transaction_id=transaction_id,
                risk_score=risk_score,
                risk_level=risk_level,
                analyst_notes=notes,
            )

            return ActionResult(
                success=True,
                action=ActionType.CREATE_CASE.value,
                message=f"Investigation case {case_record.get('case_id')} recorded successfully.",
                data=case_record,
            )
        except Exception as exc:
            return ActionResult(
                success=False,
                action=ActionType.CREATE_CASE.value,
                message=f"Case creation failed: {exc}",
            )