"""
AURA Case Management & Audit Store
----------------------------------
Thread-safe SQLite storage for fraud investigation cases, analyst notes,
and compliance audit logs.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "database" / "aura.db"


class CaseStore:
    """Manages persistent case records and investigation audit logs."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=15.0,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL UNIQUE,
                    risk_score REAL DEFAULT 0.0,
                    risk_level TEXT DEFAULT 'UNKNOWN',
                    status TEXT DEFAULT 'OPEN',
                    priority TEXT DEFAULT 'MEDIUM',
                    assigned_analyst TEXT DEFAULT 'AURA_AGENT',
                    analyst_notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS case_audit_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES cases (case_id) ON DELETE CASCADE
                );
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cases_transaction_id
                ON cases (transaction_id);
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cases_status
                ON cases (status);
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_case_audit_logs_case_id
                ON case_audit_logs (case_id);
            """)
            conn.commit()

    # ------------------------------------------------------------------
    # CASE CRUD OPERATIONS
    # ------------------------------------------------------------------

    def create_case(
        self,
        transaction_id: str,
        risk_score: float = 0.0,
        risk_level: str = "UNKNOWN",
        priority: Optional[str] = None,
        analyst_notes: str = "",
        assigned_analyst: str = "AURA_AGENT",
    ) -> Dict[str, Any]:
        """
        Create a new investigation case or return the existing case
        if already opened for this transaction.
        """
        transaction_id = str(transaction_id).strip()

        # Check if case already exists
        existing = self.get_case_by_transaction(transaction_id)
        if existing:
            # If notes provided, append them to existing case
            if analyst_notes:
                updated_notes = (
                    f"{existing['analyst_notes']}\n"
                    f"[{datetime.now(timezone.utc).isoformat()}] {analyst_notes}"
                ).strip()
                self.update_case(
                    case_id=existing["case_id"],
                    analyst_notes=updated_notes,
                )
                existing = self.get_case(existing["case_id"])
            return existing

        # Auto-determine priority from risk score if not explicitly set
        if not priority:
            if risk_score >= 80:
                priority = "CRITICAL"
            elif risk_score >= 60:
                priority = "HIGH"
            elif risk_score >= 30:
                priority = "MEDIUM"
            else:
                priority = "LOW"

        now_iso = datetime.now(timezone.utc).isoformat()
        short_id = uuid.uuid4().hex[:8].upper()
        case_id = f"CASE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{short_id}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO cases (
                    case_id, transaction_id, risk_score, risk_level,
                    status, priority, assigned_analyst, analyst_notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'OPEN', ?, ?, ?, ?, ?)
                """,
                (
                    case_id,
                    transaction_id,
                    float(risk_score),
                    str(risk_level).upper(),
                    str(priority).upper(),
                    str(assigned_analyst),
                    str(analyst_notes),
                    now_iso,
                    now_iso,
                ),
            )

            conn.execute(
                """
                INSERT INTO case_audit_logs (case_id, action, details, created_at)
                VALUES (?, 'CASE_CREATED', ?, ?)
                """,
                (
                    case_id,
                    f"Case created for transaction {transaction_id} with initial risk {risk_score} ({risk_level}).",
                    now_iso,
                ),
            )
            conn.commit()

        return self.get_case(case_id) or {}

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve case record by case_id."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM cases WHERE case_id = ?",
                (case_id.strip(),),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def get_case_by_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve case record by transaction_id."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM cases WHERE transaction_id = ?",
                (transaction_id.strip(),),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def list_cases(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List cases with optional status or priority filtering."""
        query = "SELECT * FROM cases WHERE 1=1"
        params: List[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status.strip().upper())

        if priority:
            query += " AND priority = ?"
            params.append(priority.strip().upper())

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_case(
        self,
        case_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        analyst_notes: Optional[str] = None,
        assigned_analyst: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update case attributes and log changes to audit trail."""
        case_id = case_id.strip()
        existing = self.get_case(case_id)
        if not existing:
            return None

        updates = []
        params = []
        log_entries = []
        now_iso = datetime.now(timezone.utc).isoformat()

        if status and status.upper() != existing["status"]:
            updates.append("status = ?")
            new_status = status.upper()
            params.append(new_status)
            log_entries.append(f"Status changed from {existing['status']} to {new_status}")

        if priority and priority.upper() != existing["priority"]:
            updates.append("priority = ?")
            new_priority = priority.upper()
            params.append(new_priority)
            log_entries.append(f"Priority changed from {existing['priority']} to {new_priority}")

        if analyst_notes is not None:
            updates.append("analyst_notes = ?")
            params.append(analyst_notes)
            log_entries.append("Analyst notes updated")

        if assigned_analyst and assigned_analyst != existing["assigned_analyst"]:
            updates.append("assigned_analyst = ?")
            params.append(assigned_analyst)
            log_entries.append(f"Assigned analyst changed to {assigned_analyst}")

        if not updates:
            return existing

        updates.append("updated_at = ?")
        params.append(now_iso)
        params.append(case_id)

        with self._get_connection() as conn:
            conn.execute(
                f"UPDATE cases SET {', '.join(updates)} WHERE case_id = ?",
                params,
            )

            for entry in log_entries:
                conn.execute(
                    """
                    INSERT INTO case_audit_logs (case_id, action, details, created_at)
                    VALUES (?, 'CASE_UPDATED', ?, ?)
                    """,
                    (case_id, entry, now_iso),
                )
            conn.commit()

        return self.get_case(case_id)

    def get_audit_logs(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieve chronological audit trail for a case."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM case_audit_logs WHERE case_id = ? ORDER BY created_at ASC",
                (case_id.strip(),),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """Aggregate summary statistics across all cases."""
        with self._get_connection() as conn:
            total_cases = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]

            status_rows = conn.execute(
                "SELECT status, COUNT(*) as count FROM cases GROUP BY status"
            ).fetchall()
            status_counts = {row["status"]: row["count"] for row in status_rows}

            priority_rows = conn.execute(
                "SELECT priority, COUNT(*) as count FROM cases GROUP BY priority"
            ).fetchall()
            priority_counts = {row["priority"]: row["count"] for row in priority_rows}

            high_risk_cases = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE risk_score >= 70"
            ).fetchone()[0]

            return {
                "total_cases": total_cases,
                "status_distribution": status_counts,
                "priority_distribution": priority_counts,
                "high_risk_cases_count": high_risk_cases,
            }
