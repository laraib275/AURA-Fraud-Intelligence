"""Unit tests for AURA Action Router and Executor using standard unittest."""

import unittest
from src.agents.action_router import AURAActionRouter, ActionType, ActionDecision
from src.agents.action_executor import AURAActionExecutor, ActionResult


class TestAURAActionRouter(unittest.TestCase):

    def setUp(self):
        self.router = AURAActionRouter()
        self.executor = AURAActionExecutor(pipeline=None)

    def test_router_normal_question(self):
        decision = self.router.route("Why was this transaction flagged as suspicious?")
        self.assertEqual(decision.action, ActionType.ANSWER_QUESTION)
        self.assertFalse(decision.explicit_request)

    def test_router_generate_pdf(self):
        decision = self.router.route("Please generate a pdf report for this transaction")
        self.assertEqual(decision.action, ActionType.GENERATE_PDF)
        self.assertTrue(decision.explicit_request)
        self.assertGreaterEqual(decision.confidence, 0.8)

    def test_router_generate_video(self):
        decision = self.router.route("Create an investigation video recording for this case")
        self.assertEqual(decision.action, ActionType.GENERATE_VIDEO)
        self.assertTrue(decision.explicit_request)
        self.assertGreaterEqual(decision.confidence, 0.8)

    def test_router_ceo_summary(self):
        decision = self.router.route("Prepare an executive summary for our leadership team")
        self.assertEqual(decision.action, ActionType.GENERATE_CEO_SUMMARY)
        self.assertTrue(decision.explicit_request)
        self.assertGreaterEqual(decision.confidence, 0.8)

    def test_router_create_case(self):
        decision = self.router.route("Create a new investigation case for this fraud event")
        self.assertEqual(decision.action, ActionType.CREATE_CASE)
        self.assertTrue(decision.explicit_request)

    def test_executor_empty_question(self):
        decision = ActionDecision(
            action=ActionType.ANSWER_QUESTION,
            confidence=1.0,
            explicit_request=False,
            reason="test",
        )
        result = self.executor.execute(decision=decision, question="")
        self.assertFalse(result.success)
        self.assertIn("No question", result.message)

    def test_executor_pdf_requires_transaction_id(self):
        decision = ActionDecision(
            action=ActionType.GENERATE_PDF,
            confidence=1.0,
            explicit_request=True,
            reason="test",
        )
        result = self.executor.execute(decision=decision, transaction_id=None)
        self.assertFalse(result.success)
        self.assertIn("transaction ID is required", result.message)

    def test_executor_video_requires_transaction_id(self):
        decision = ActionDecision(
            action=ActionType.GENERATE_VIDEO,
            confidence=1.0,
            explicit_request=True,
            reason="test",
        )
        result = self.executor.execute(decision=decision, transaction_id="")
        self.assertFalse(result.success)
        self.assertIn("transaction ID is required", result.message)

    def test_executor_ceo_summary_requires_transaction_id(self):
        decision = ActionDecision(
            action=ActionType.GENERATE_CEO_SUMMARY,
            confidence=1.0,
            explicit_request=True,
            reason="test",
        )
        result = self.executor.execute(decision=decision, transaction_id=None)
        self.assertFalse(result.success)
        self.assertIn("transaction ID is required", result.message)


if __name__ == "__main__":
    unittest.main()
