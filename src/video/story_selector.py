from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class StoryProfile:
    story_type: str
    title: str
    objective: str
    emphasis: List[str]
    priority: int


class DynamicStorySelector:
    """
    Selects the video narrative using evidence already produced by AURA.

    AUTO policy:
        CRITICAL -> Full AURA Investigation
        HIGH     -> Full Investigation unless a specialized signal
                    is clearly dominant
        MEDIUM   -> Dynamic evidence-based selection
        LOW      -> Risk Review unless a specialized signal is dominant
    """

    def select(self, investigation_result: Dict[str, Any]) -> Dict[str, Any]:
        investigation = investigation_result.get("investigation", {})

        risk_score = self._to_float(investigation.get("risk_score"), 0.0)
        risk_band = str(investigation.get("risk_band", "UNKNOWN")).upper()

        graph_score = self._to_float(
            investigation.get("graph_risk_score"), 0.0
        )
        graph_band = str(
            investigation.get("graph_risk_band", "UNKNOWN")
        ).upper()

        behavioural_risk = self._to_float(
            investigation.get("behavioural_risk_score"), 0.0
        )
        anomaly_risk = self._to_float(
            investigation.get("anomaly_risk"), 0.0
        )
        amount_risk = self._to_float(
            investigation.get("amount_risk"), 0.0
        )
        velocity_risk = self._to_float(
            investigation.get("velocity_risk"), 0.0
        )
        novelty_risk = self._to_float(
            investigation.get("novelty_risk"), 0.0
        )

        investigation_reasons = investigation.get(
            "investigation_reasons", []
        )
        graph_reasons = investigation.get("graph_reasons", [])

        candidates = self._build_candidates(
            risk_score,
            risk_band,
            graph_score,
            graph_band,
            behavioural_risk,
            anomaly_risk,
            amount_risk,
            velocity_risk,
            novelty_risk,
            investigation_reasons,
            graph_reasons,
        )

        selected = self._select_auto_story(
            candidates, risk_score, risk_band
        )

        return {
            "selection_mode": "AUTO",
            "selected_story": asdict(selected),
            "candidate_stories": [
                asdict(profile)
                for profile in sorted(
                    candidates,
                    key=lambda profile: profile.priority,
                    reverse=True,
                )
            ],
            "evidence_summary": {
                "risk_score": risk_score,
                "risk_band": risk_band,
                "graph_risk_score": graph_score,
                "graph_risk_band": graph_band,
                "behavioural_risk": behavioural_risk,
                "anomaly_risk": anomaly_risk,
                "amount_risk": amount_risk,
                "velocity_risk": velocity_risk,
                "novelty_risk": novelty_risk,
                "investigation_reason_count": len(investigation_reasons),
                "graph_reason_count": len(graph_reasons),
            },
        }

    def _select_auto_story(
        self,
        candidates: List[StoryProfile],
        risk_score: float,
        risk_band: str,
    ) -> StoryProfile:
        """Apply AURA's default automatic story policy."""

        full_story = next(
            profile
            for profile in candidates
            if profile.story_type == "full_investigation"
        )

        if risk_band == "CRITICAL" or risk_score >= 80:
            return full_story

        if risk_band == "HIGH" or risk_score >= 60:
            strongest = max(
                candidates,
                key=lambda profile: profile.priority,
            )

            if strongest.story_type == "full_investigation":
                return strongest

            if strongest.priority >= full_story.priority + 20:
                return strongest

            return full_story

        return max(
            candidates,
            key=lambda profile: profile.priority,
        )

    def _build_candidates(
        self,
        risk_score: float,
        risk_band: str,
        graph_score: float,
        graph_band: str,
        behavioural_risk: float,
        anomaly_risk: float,
        amount_risk: float,
        velocity_risk: float,
        novelty_risk: float,
        investigation_reasons: List[Any],
        graph_reasons: List[Any],
    ) -> List[StoryProfile]:

        candidates: List[StoryProfile] = []

        full_priority = 20
        if risk_band == "CRITICAL":
            full_priority += 30
        elif risk_band == "HIGH":
            full_priority += 20
        elif risk_score >= 60:
            full_priority += 15

        if len(investigation_reasons) >= 3:
            full_priority += 10
        if anomaly_risk >= 70:
            full_priority += 5
        if behavioural_risk >= 70:
            full_priority += 5

        candidates.append(
            StoryProfile(
                "full_investigation",
                "Full AURA Investigation",
                "Present the transaction as a complete fraud-investigation case using the strongest available AURA evidence.",
                [
                    "transaction",
                    "behavioural risk",
                    "anomaly detection",
                    "overall AURA risk",
                    "graph intelligence",
                    "AI investigation",
                    "recommended action",
                ],
                full_priority,
            )
        )

        anomaly_priority = 15
        if anomaly_risk >= 70:
            anomaly_priority += 35
        elif anomaly_risk >= 50:
            anomaly_priority += 20
        elif anomaly_risk >= 30:
            anomaly_priority += 10

        candidates.append(
            StoryProfile(
                "anomaly_investigation",
                "Anomaly Investigation",
                "Explain how the transaction differs from expected transactional behaviour.",
                [
                    "anomaly signal",
                    "unusual behaviour",
                    "transaction deviation",
                    "AURA risk assessment",
                    "investigation decision",
                ],
                anomaly_priority,
            )
        )

        behavioural_priority = 15
        if behavioural_risk >= 80:
            behavioural_priority += 35
        elif behavioural_risk >= 60:
            behavioural_priority += 25
        elif behavioural_risk >= 40:
            behavioural_priority += 10

        candidates.append(
            StoryProfile(
                "behavioural_investigation",
                "Behavioural Risk Investigation",
                "Show how the transaction compares with the customer's established behaviour.",
                [
                    "customer behaviour",
                    "velocity",
                    "amount behaviour",
                    "merchant novelty",
                    "behavioural risk",
                    "overall AURA risk",
                ],
                behavioural_priority,
            )
        )

        network_priority = 10
        if graph_score >= 70:
            network_priority += 40
        elif graph_score >= 50:
            network_priority += 30
        elif graph_score >= 30:
            network_priority += 15

        if graph_band == "CRITICAL":
            network_priority += 20
        elif graph_band == "HIGH":
            network_priority += 15

        if graph_reasons:
            network_priority += 10

        candidates.append(
            StoryProfile(
                "network_investigation",
                "Network Intelligence Investigation",
                "Reveal relationships between the transaction and surrounding risk entities.",
                [
                    "transaction network",
                    "connected transactions",
                    "graph risk",
                    "network relationships",
                    "AI investigation",
                    "recommended action",
                ],
                network_priority,
            )
        )

        transaction_priority = 10
        if amount_risk >= 80:
            transaction_priority += 20
        if velocity_risk >= 80:
            transaction_priority += 20
        if novelty_risk >= 80:
            transaction_priority += 15
        if amount_risk >= 60 and velocity_risk >= 60:
            transaction_priority += 20

        candidates.append(
            StoryProfile(
                "transaction_behaviour",
                "Transaction Behaviour Investigation",
                "Explain the specific transaction-level signals that triggered AURA's attention.",
                [
                    "transaction amount",
                    "transaction velocity",
                    "merchant novelty",
                    "behavioural signals",
                    "risk assessment",
                ],
                transaction_priority,
            )
        )

        review_priority = 5
        if risk_band in {"LOW", "MEDIUM"}:
            review_priority += 20
        if risk_score < 30:
            review_priority += 20
        if (
            anomaly_risk < 30
            and behavioural_risk < 30
            and graph_score < 30
        ):
            review_priority += 20

        candidates.append(
            StoryProfile(
                "risk_review",
                "AURA Risk Review",
                "Provide a balanced explanation of why the transaction was reviewed without overstating fraud evidence.",
                [
                    "transaction context",
                    "available risk signals",
                    "AURA risk score",
                    "graph context",
                    "review recommendation",
                ],
                review_priority,
            )
        )

        return candidates

    @staticmethod
    def _to_float(value: Any, default: float) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def select_story(
        self,
        investigation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self.select(investigation_result)
