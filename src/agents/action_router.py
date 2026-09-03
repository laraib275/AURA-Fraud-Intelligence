"""
AURA Action Router

Converts natural-language Ask AURA requests into deterministic actions.

Important:
- Questions remain questions.
- Generation happens ONLY when explicitly requested.
- No automatic PDF/video/case generation.
"""

from dataclasses import dataclass
from enum import Enum
import re


class ActionType(str, Enum):
    ANSWER_QUESTION = "answer_question"
    GENERATE_PDF = "generate_pdf"
    GENERATE_VIDEO = "generate_video"
    GENERATE_CEO_SUMMARY = "generate_ceo_summary"
    ANALYZE_TRANSACTIONS = "analyze_transactions"
    CREATE_CASE = "create_case"


@dataclass
class ActionDecision:
    action: ActionType
    confidence: float
    explicit_request: bool
    reason: str


class AURAActionRouter:
    """
    Deterministic first-stage action router.

    The router deliberately uses explicit language for generation actions
    so AURA does not accidentally create files or execute actions.
    """

    PDF_WORDS = (
        "pdf",
        "report",
        "document",
    )

    VIDEO_WORDS = (
        "video",
        "mp4",
        "recording",
        "investigation video",
    )

    GENERATE_WORDS = (
        "generate",
        "create",
        "make",
        "produce",
        "export",
        "download",
        "save",
        "prepare",
    )

    CEO_WORDS = (
        "ceo summary",
        "executive summary",
        "executive brief",
        "management summary",
        "leadership summary",
        "board summary",
    )

    MULTI_TRANSACTION_WORDS = (
        "transactions",
        "multiple transactions",
        "several transactions",
        "transaction ids",
        "batch analysis",
        "compare transactions",
        "compare these",
    )

    CASE_WORDS = (
        "create a case",
        "open a case",
        "create case",
        "open case",
        "raise a case",
        "investigation case",
    )

    def route(self, question: str) -> ActionDecision:
        if not question or not question.strip():
            return ActionDecision(
                action=ActionType.ANSWER_QUESTION,
                confidence=1.0,
                explicit_request=False,
                reason="Empty request defaults to conversational response.",
            )

        text = self._normalize(question)

        # ---------------------------------------------------------
        # 1. Explicit PDF generation
        # ---------------------------------------------------------
        if self._contains_any(text, self.PDF_WORDS) and self._contains_any(
            text, self.GENERATE_WORDS
        ):
            return ActionDecision(
                action=ActionType.GENERATE_PDF,
                confidence=0.99,
                explicit_request=True,
                reason="User explicitly requested PDF/report generation.",
            )

        # ---------------------------------------------------------
        # 2. Explicit video generation
        # ---------------------------------------------------------
        if self._contains_any(text, self.VIDEO_WORDS) and self._contains_any(
            text, self.GENERATE_WORDS
        ):
            return ActionDecision(
                action=ActionType.GENERATE_VIDEO,
                confidence=0.99,
                explicit_request=True,
                reason="User explicitly requested video generation.",
            )

        # ---------------------------------------------------------
        # 3. Explicit CEO / executive summary generation
        # ---------------------------------------------------------
        if self._contains_any(text, self.CEO_WORDS) and self._contains_any(
            text, self.GENERATE_WORDS
        ):
            return ActionDecision(
                action=ActionType.GENERATE_CEO_SUMMARY,
                confidence=0.97,
                explicit_request=True,
                reason="User explicitly requested executive intelligence.",
            )

        # ---------------------------------------------------------
        # 4. Multi-transaction analysis
        # ---------------------------------------------------------
        if self._contains_any(text, self.MULTI_TRANSACTION_WORDS):
            return ActionDecision(
                action=ActionType.ANALYZE_TRANSACTIONS,
                confidence=0.95,
                explicit_request=True,
                reason="Request references multiple transactions or comparison.",
            )

        # ---------------------------------------------------------
        # 5. Case creation
        # ---------------------------------------------------------
        if self._contains_any(text, self.CASE_WORDS):
            return ActionDecision(
                action=ActionType.CREATE_CASE,
                confidence=0.99,
                explicit_request=True,
                reason="User explicitly requested case creation.",
            )

        # ---------------------------------------------------------
        # 6. Everything else remains conversational
        # ---------------------------------------------------------
        return ActionDecision(
            action=ActionType.ANSWER_QUESTION,
            confidence=0.95,
            explicit_request=False,
            reason="No explicit executable action detected; answer conversationally.",
        )

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _contains_any(text: str, phrases) -> bool:
        return any(phrase in text for phrase in phrases)


if __name__ == "__main__":
    router = AURAActionRouter()

    test_requests = [
        "Why is this transaction high risk?",
        "Explain why this transaction is critical",
        "Generate the investigation PDF",
        "Create a PDF report for this transaction",
        "Create a 60 second investigation video",
        "Generate an executive summary",
        "Analyze these transactions",
        "Create a case for this transaction",
    ]

    for request in test_requests:
        decision = router.route(request)

        print("\nREQUEST:", request)
        print("ACTION:", decision.action.value)
        print("EXPLICIT:", decision.explicit_request)
        print("CONFIDENCE:", decision.confidence)
        print("REASON:", decision.reason)