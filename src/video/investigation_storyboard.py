from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class StoryboardScene:
    scene_number: int
    title: str
    duration_seconds: float
    visual: str
    narration: str
    on_screen_text: str
    data_points: Dict[str, Any]


class InvestigationStoryboard:
    """
    Converts an AURA investigation result into a structured,
    presentation-ready cinematic storyboard.

    This module does NOT perform fraud detection.
    It only transforms existing investigation results into
    video storytelling instructions.
    """

    def __init__(self, target_duration: int = 60):
        self.target_duration = target_duration

    def build(self, investigation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a cinematic storyboard from the AURA investigation result.
        """

        investigation = investigation_result.get("investigation", {})
        ai_report = investigation_result.get("ai_report", {})

        transaction_id = str(
            investigation.get("transaction_id", "UNKNOWN")
        )

        amount = investigation.get("amount", "N/A")
        risk_score = investigation.get("risk_score", "N/A")
        risk_band = str(
            investigation.get("risk_band", "UNKNOWN")
        ).upper()

        graph_score = investigation.get("graph_risk_score", "N/A")
        graph_band = str(
            investigation.get("graph_risk_band", "UNKNOWN")
        ).upper()

        fraud_probability = investigation.get(
            "fraud_probability", "N/A"
        )

        investigation_flag = investigation.get(
            "investigation_flag", False
        )

        recommended_action = investigation.get(
            "recommended_action",
            "REVIEW TRANSACTION",
        )

        reasons = investigation.get(
            "investigation_reasons",
            [],
        )

        graph_reasons = investigation.get(
            "graph_reasons",
            [],
        )

        top_risk_factors = investigation.get(
            "top_risk_factors",
            [],
        )

        scenes = [
            self._scene_transaction_detected(
                transaction_id=transaction_id,
                amount=amount,
            ),
            self._scene_suspicious_activity(
                reasons=reasons,
                top_risk_factors=top_risk_factors,
            ),
            self._scene_aura_risk(
                risk_score=risk_score,
                risk_band=risk_band,
                fraud_probability=fraud_probability,
            ),
            self._scene_graph_analysis(
                graph_score=graph_score,
                graph_band=graph_band,
                graph_reasons=graph_reasons,
            ),
            self._scene_ai_investigator(
                ai_report=ai_report,
            ),
            self._scene_action(
                investigation_flag=investigation_flag,
                recommended_action=recommended_action,
            ),
        ]

        total_duration = sum(
            scene.duration_seconds for scene in scenes
        )

        return {
            "title": "AURA AI Fraud Investigation",
            "format": "16:9",
            "target_duration_seconds": self.target_duration,
            "actual_duration_seconds": round(total_duration, 2),
            "visual_style": (
                "premium 2.5D cinematic financial-crime investigation"
            ),
            "brand_identity": {
                "name": "AURA",
                "primary_visual_theme": "pink",
                "tone": "professional, intelligent, trustworthy",
            },
            "transaction_id": transaction_id,
            "risk_summary": {
                "aura_risk_score": risk_score,
                "aura_risk_band": risk_band,
                "graph_risk_score": graph_score,
                "graph_risk_band": graph_band,
                "fraud_probability": fraud_probability,
            },
            "scenes": [
                asdict(scene)
                for scene in scenes
            ],
        }

    def _scene_transaction_detected(
        self,
        transaction_id: str,
        amount: Any,
    ) -> StoryboardScene:

        return StoryboardScene(
            scene_number=1,
            title="The Transaction",
            duration_seconds=8,
            visual=(
                "A premium cinematic financial environment. "
                "A glowing transaction card appears in the center "
                "of a sophisticated digital payment network. "
                "The transaction amount becomes visually prominent."
            ),
            narration=(
                "AURA begins with a single transaction. "
                "At first glance, it appears to be an ordinary payment."
            ),
            on_screen_text=(
                f"TRANSACTION\n"
                f"{transaction_id}\n"
                f"AMOUNT: {amount}"
            ),
            data_points={
                "transaction_id": transaction_id,
                "amount": amount,
            },
        )

    def _scene_suspicious_activity(
        self,
        reasons: List[Any],
        top_risk_factors: List[Dict[str, Any]],
    ) -> StoryboardScene:

        reason_text = self._format_reasons(reasons)

        factor_names = [
            str(item.get("feature"))
            for item in top_risk_factors[:4]
            if isinstance(item, dict)
        ]

        return StoryboardScene(
            scene_number=2,
            title="Suspicious Activity Emerges",
            duration_seconds=10,
            visual=(
                "The transaction card begins interacting with "
                "multiple visual signals. Behavioural patterns, "
                "velocity indicators and anomaly signals appear "
                "around the transaction as subtle animated overlays."
            ),
            narration=(
                "AURA detects signals that deserve attention. "
                + reason_text
            ),
            on_screen_text=(
                "SUSPICIOUS ACTIVITY DETECTED\n"
                + "\n".join(
                    f"• {reason}"
                    for reason in reasons[:3]
                )
            ),
            data_points={
                "investigation_reasons": reasons,
                "top_risk_factors": factor_names,
            },
        )

    def _scene_aura_risk(
        self,
        risk_score: Any,
        risk_band: str,
        fraud_probability: Any,
    ) -> StoryboardScene:

        return StoryboardScene(
            scene_number=3,
            title="AURA Risk Assessment",
            duration_seconds=10,
            visual=(
                "A large AURA risk gauge forms around the transaction. "
                "The score rises dramatically and settles on the "
                "final AURA risk assessment. The result is presented "
                "as the central decision signal."
            ),
            narration=(
                f"AURA calculates an overall risk score of "
                f"{risk_score}, classified as {risk_band}. "
                f"The machine-learning fraud probability is "
                f"{fraud_probability}."
            ),
            on_screen_text=(
                f"AURA RISK SCORE\n"
                f"{risk_score}\n"
                f"{risk_band}\n\n"
                f"ML FRAUD PROBABILITY: {fraud_probability}"
            ),
            data_points={
                "aura_risk_score": risk_score,
                "aura_risk_band": risk_band,
                "fraud_probability": fraud_probability,
            },
        )

    def _scene_graph_analysis(
        self,
        graph_score: Any,
        graph_band: str,
        graph_reasons: List[Any],
    ) -> StoryboardScene:

        return StoryboardScene(
            scene_number=4,
            title="The Hidden Network",
            duration_seconds=10,
            visual=(
                "The transaction expands into a cinematic network graph. "
                "Customer, transactions and risk connections appear "
                "as glowing nodes and links. The network reveals "
                "connections to previously identified risk."
            ),
            narration=(
                f"AURA then examines the surrounding transaction network. "
                f"The graph risk score is {graph_score}, classified as "
                f"{graph_band}. "
                "The network also reveals important connections "
                "that warrant investigation."
            ),
            on_screen_text=(
                f"GRAPH RISK SCORE\n"
                f"{graph_score}\n"
                f"{graph_band}"
            ),
            data_points={
                "graph_risk_score": graph_score,
                "graph_risk_band": graph_band,
                "graph_reasons": graph_reasons,
            },
        )

    def _scene_ai_investigator(
        self,
        ai_report: Any,
    ) -> StoryboardScene:

        if isinstance(ai_report, dict):
            ai_analysis = (
                ai_report.get("analysis")
                or ai_report.get("summary")
                or ai_report.get("ai_analysis")
                or ""
            )
        else:
            ai_analysis = str(ai_report)

        if not ai_analysis:
            ai_analysis = (
                "AURA's AI Investigator synthesizes the available "
                "evidence into an investigation narrative."
            )

        return StoryboardScene(
            scene_number=5,
            title="AI Investigator",
            duration_seconds=10,
            visual=(
                "AURA's digital investigator interface activates. "
                "Evidence streams converge into a single investigation "
                "timeline. Key findings are organized into a clear "
                "human-readable explanation."
            ),
            narration=(
                "AURA's AI Investigator brings the evidence together, "
                "connecting the transaction, behavioural signals, "
                "anomalies and network intelligence into one investigation."
            ),
            on_screen_text=(
                "AI INVESTIGATOR\n"
                "EVIDENCE SYNTHESIS"
            ),
            data_points={
                "ai_analysis_available": bool(ai_analysis),
                "ai_analysis": ai_analysis,
            },
        )

    def _scene_action(
        self,
        investigation_flag: bool,
        recommended_action: str,
    ) -> StoryboardScene:

        action = str(recommended_action).upper()

        return StoryboardScene(
            scene_number=6,
            title="Investigation Decision",
            duration_seconds=12,
            visual=(
                "The network fades into a clean executive decision scene. "
                "The AURA intelligence panel remains visible while "
                "the recommended investigation action appears with "
                "a strong cinematic emphasis."
            ),
            narration=(
                f"AURA recommends: {action}. "
                "The investigation can now move from detection "
                "to human review and action."
            ),
            on_screen_text=(
                f"INVESTIGATION DECISION\n"
                f"{action}"
            ),
            data_points={
                "investigation_flag": investigation_flag,
                "recommended_action": recommended_action,
            },
        )

    @staticmethod
    def _format_reasons(reasons: List[Any]) -> str:

        if not reasons:
            return (
                "Additional behavioural and anomaly signals "
                "require further review."
            )

        clean_reasons = [
            str(reason)
            for reason in reasons[:3]
        ]

        return " ".join(clean_reasons)

    def to_dict(
        self,
        investigation_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        return self.build(investigation_result)