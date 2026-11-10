"""Unit tests for AURA Case Management and Database Store."""

import os
import tempfile
import unittest
from pathlib import Path

from database.case_store import CaseStore


class TestCaseStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_cases.db"
        self.store = CaseStore(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_get_case(self):
        case = self.store.create_case(
            transaction_id="TXN-1001",
            risk_score=85.0,
            risk_level="CRITICAL",
            analyst_notes="Test investigation case",
        )
        self.assertTrue(case["case_id"].startswith("CASE-"))
        self.assertEqual(case["transaction_id"], "TXN-1001")
        self.assertEqual(case["risk_score"], 85.0)
        self.assertEqual(case["priority"], "CRITICAL")
        self.assertEqual(case["status"], "OPEN")

        # Retrieve by case_id
        fetched = self.store.get_case(case["case_id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["case_id"], case["case_id"])

        # Retrieve by transaction_id
        by_txn = self.store.get_case_by_transaction("TXN-1001")
        self.assertIsNotNone(by_txn)
        self.assertEqual(by_txn["case_id"], case["case_id"])

    def test_duplicate_case_appends_notes(self):
        case1 = self.store.create_case(
            transaction_id="TXN-DUP-01",
            risk_score=72.0,
            risk_level="HIGH",
            analyst_notes="Initial note",
        )
        case2 = self.store.create_case(
            transaction_id="TXN-DUP-01",
            risk_score=72.0,
            risk_level="HIGH",
            analyst_notes="Secondary note",
        )
        self.assertEqual(case1["case_id"], case2["case_id"])
        self.assertIn("Initial note", case2["analyst_notes"])
        self.assertIn("Secondary note", case2["analyst_notes"])

    def test_update_case_and_audit_trail(self):
        case = self.store.create_case(
            transaction_id="TXN-AUDIT-01",
            risk_score=45.0,
            risk_level="MEDIUM",
        )
        case_id = case["case_id"]

        updated = self.store.update_case(
            case_id=case_id,
            status="UNDER_REVIEW",
            priority="HIGH",
            analyst_notes="Escalated to senior fraud analyst.",
        )
        self.assertEqual(updated["status"], "UNDER_REVIEW")
        self.assertEqual(updated["priority"], "HIGH")

        logs = self.store.get_audit_logs(case_id)
        self.assertGreaterEqual(len(logs), 2)  # Created + Updated
        actions = [log["action"] for log in logs]
        self.assertIn("CASE_CREATED", actions)
        self.assertIn("CASE_UPDATED", actions)

    def test_list_cases_and_stats(self):
        self.store.create_case("TXN-A", risk_score=90.0, risk_level="CRITICAL")
        self.store.create_case("TXN-B", risk_score=20.0, risk_level="LOW")
        self.store.create_case("TXN-C", risk_score=65.0, risk_level="HIGH")

        cases = self.store.list_cases()
        self.assertEqual(len(cases), 3)

        stats = self.store.get_statistics()
        self.assertEqual(stats["total_cases"], 3)
        self.assertEqual(stats["status_distribution"].get("OPEN"), 3)
        self.assertGreaterEqual(stats["high_risk_cases_count"], 1)


if __name__ == "__main__":
    unittest.main()
