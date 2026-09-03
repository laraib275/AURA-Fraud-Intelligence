from dataclasses import dataclass
from typing import Any, Dict, Optional

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

    def __init__(self, pipeline=None):
        self.pipeline = pipeline

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
            )

        # ---------------------------------------------------------
        # 4. CEO EXECUTIVE SUMMARY
        # ---------------------------------------------------------
        if action == ActionType.GENERATE_CEO_SUMMARY:
            return self._generate_ceo_summary(
                transaction_id=transaction_id,
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
    # GENERATE VIDEO
    # =============================================================

    def _generate_video(
        self,
        transaction_id: Optional[str],
    ) -> ActionResult:

        if not transaction_id:
            return ActionResult(
                success=False,
                action=ActionType.GENERATE_VIDEO.value,
                message="A transaction ID is required to generate an investigation video.",
            )

        return ActionResult(
            success=True,
            action=ActionType.GENERATE_VIDEO.value,
            message="Video generation requested.",
            data={
                "transaction_id": transaction_id,
                "requires_video_generation": True,
            },
        )

    # =============================================================
    # CEO EXECUTIVE SUMMARY
    # =============================================================

    def _generate_ceo_summary(
        self,
        transaction_id: Optional[str],
    ) -> ActionResult:

        return ActionResult(
            success=True,
            action=ActionType.GENERATE_CEO_SUMMARY.value,
            message="Executive intelligence generation requested.",
            data={
                "transaction_id": transaction_id,
                "requires_ceo_summary": True,
            },
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
    ) -> ActionResult:

        if not transaction_id:
            return ActionResult(
                success=False,
                action=ActionType.CREATE_CASE.value,
                message="A transaction ID is required to create a case.",
            )

        return ActionResult(
            success=True,
            action=ActionType.CREATE_CASE.value,
            message="Fraud investigation case creation requested.",
            data={
                "transaction_id": transaction_id,
                "requires_case_creation": True,
            },
        )