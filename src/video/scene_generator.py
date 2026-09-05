"""
AURA Fraud Intelligence
-----------------------
Scene Generator for cinematic investigation videos.

Purpose:
    Convert an AURA investigation result + selected story into a structured,
    renderer-ready sequence of cinematic scenes.

This module does NOT render video, call an image/video model, or generate
audio. It is intentionally a presentation-layer component.

Expected flow:
    Investigation Pipeline
            ↓
    Dynamic Story Selector
            ↓
    Scene Generator
            ↓
    Video Renderer
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Scene:
    """Renderer-ready description of one cinematic scene."""

    scene_number: int
    scene_type: str
    title: str
    duration: int
    purpose: str
    visual_environment: str
    visual_action: str
    camera: str
    objects: List[str]
    overlays: List[str]
    narration: str
    transition: str


class SceneGenerator:
    """
    Generate cinematic scene specifications from an AURA investigation.

    The generator is evidence-driven: important values such as AURA risk,
    graph risk, amount, anomaly risk, and behavioural risk are read from
    the supplied investigation result rather than hard-coded.
    """

    DEFAULT_DURATION = 60

    def generate(
        self,
        investigation_result: Dict[str, Any],
        selected_story: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a renderer-ready video scene plan.

        Parameters
        ----------
        investigation_result:
            Output from AIInvestigationPipeline.investigate().
        selected_story:
            Output from DynamicStorySelector.select()['selected_story'].
            If omitted, the generator derives the story type from the
            investigation risk band.

        Returns
        -------
        dict
            JSON-friendly scene plan.
        """

        investigation = investigation_result.get("investigation", {})
        if not isinstance(investigation, dict):
            investigation = {}

        story = selected_story or self._fallback_story(investigation)

        story_type = str(
            story.get("story_type", "full_investigation")
        ).strip().lower()

        evidence = self._extract_evidence(investigation)

        scenes = self._build_scenes(
            story_type=story_type,
            evidence=evidence,
        )

        total_duration = sum(scene.duration for scene in scenes)

        return {
            "video_title": self._video_title(story_type),
            "story_type": story_type,
            "selection_mode": (
                "AUTO"
                if selected_story is None
                else str(selected_story.get("selection_mode", "AUTO"))
            ),
            "duration_seconds": total_duration,
            "aspect_ratio": "16:9",
            "visual_style": (
                "Premium 2.5D cinematic financial-investigation style"
            ),
            "brand": {
                "name": "AURA",
                "identity": "AI Fraud Intelligence",
                "visual_direction": (
                    "Elegant pink-accented AI investigation environment, "
                    "professional financial-security aesthetic"
                ),
            },
            "evidence_summary": evidence,
            "scenes": [asdict(scene) for scene in scenes],
        }

    def _extract_evidence(self, investigation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only the evidence required by the visual story."""

        graph_analysis = investigation.get("graph_analysis", {})
        if not isinstance(graph_analysis, dict):
            graph_analysis = {}

        graph_metrics = graph_analysis.get("graph_metrics", {})
        if not isinstance(graph_metrics, dict):
            graph_metrics = {}

        # Backward compatibility with older investigation structures.
        if not graph_analysis:
            graph_analysis = {
                "graph_risk_score": investigation.get("graph_risk_score"),
                "graph_risk_band": investigation.get("graph_risk_band"),
                "graph_metrics": investigation.get("graph_metrics", {}),
                "graph_reasons": investigation.get("graph_reasons", []),
            }
            graph_metrics = graph_analysis.get("graph_metrics", {}) or {}

        reasons = investigation.get("investigation_reasons", [])
        if not isinstance(reasons, list):
            reasons = [str(reasons)]

        graph_reasons = graph_analysis.get("graph_reasons", [])
        if hasattr(graph_reasons, "tolist"):
            graph_reasons = graph_reasons.tolist()
        if not isinstance(graph_reasons, list):
            graph_reasons = [str(graph_reasons)]

        top_risk_factors = investigation.get("top_risk_factors", [])
        if not isinstance(top_risk_factors, list):
            top_risk_factors = []

        return {
            "transaction_id": str(
                investigation.get("transaction_id", "UNKNOWN")
            ),
            "transaction_time": str(
                investigation.get("transaction_time", "UNKNOWN")
            ),
            "amount": self._number(investigation.get("amount")),
            "currency": "USD",
            "risk_score": self._number(investigation.get("risk_score")),
            "risk_band": str(
                investigation.get("risk_band", "UNKNOWN")
            ).upper(),
            "fraud_probability": self._number(
                investigation.get("fraud_probability")
            ),
            "investigation_flag": bool(
                investigation.get("investigation_flag", False)
            ),
            "recommended_action": str(
                investigation.get(
                    "recommended_action",
                    "REVIEW",
                )
            ),
            "amount_risk": self._number(
                investigation.get("amount_risk")
            ),
            "velocity_risk": self._number(
                investigation.get("velocity_risk")
            ),
            "novelty_risk": self._number(
                investigation.get("novelty_risk")
            ),
            "behavioural_risk_score": self._number(
                investigation.get("behavioural_risk_score")
            ),
            "anomaly_score": self._number(
                investigation.get("anomaly_score")
            ),
            "anomaly_risk": self._number(
                investigation.get("anomaly_risk")
            ),
            "investigation_reasons": [
                str(reason) for reason in reasons
            ],
            "top_risk_factors": top_risk_factors,
            "graph_risk_score": self._number(
                graph_analysis.get("graph_risk_score")
            ),
            "graph_risk_band": str(
                graph_analysis.get(
                    "graph_risk_band",
                    "UNKNOWN",
                )
            ).upper(),
            "graph_metrics": {
                "transaction_count": graph_metrics.get(
                    "transaction_count"
                ),
                "unique_merchant_count": graph_metrics.get(
                    "unique_merchant_count"
                ),
                "fraud_transaction_count": graph_metrics.get(
                    "fraud_transaction_count"
                ),
                "high_risk_transaction_count": graph_metrics.get(
                    "high_risk_transaction_count"
                ),
                "average_transaction_risk": graph_metrics.get(
                    "average_transaction_risk"
                ),
                "maximum_transaction_risk": graph_metrics.get(
                    "maximum_transaction_risk"
                ),
                "fraud_ratio": graph_metrics.get("fraud_ratio"),
                "high_risk_ratio": graph_metrics.get(
                    "high_risk_ratio"
                ),
            },
            "graph_reasons": [
                str(reason) for reason in graph_reasons
            ],
        }

    def _build_scenes(
        self,
        story_type: str,
        evidence: Dict[str, Any],
    ) -> List[Scene]:
        """Build scenes according to the selected investigation story."""

        builders = {
            "full_investigation": self._full_investigation,
            "anomaly_investigation": self._anomaly_investigation,
            "behavioural_investigation": self._behavioural_investigation,
            "network_investigation": self._network_investigation,
            "transaction_behaviour": self._transaction_behaviour,
            "risk_review": self._risk_review,
        }

        builder = builders.get(
            story_type,
            self._full_investigation,
        )

        return builder(evidence)

    # ------------------------------------------------------------------
    # Story variants
    # ------------------------------------------------------------------

    def _full_investigation(
        self,
        e: Dict[str, Any],
    ) -> List[Scene]:
        """Premium end-to-end investigation story."""

        return [
            self._transaction_scene(e, 8),
            self._suspicion_scene(e, 10),
            self._risk_scene(e, 10),
            self._network_scene(e, 10),
            self._ai_scene(e, 10),
            self._decision_scene(e, 12),
        ]

    def _anomaly_investigation(
        self,
        e: Dict[str, Any],
    ) -> List[Scene]:
        """Story focused on unusual transaction behaviour."""

        return [
            self._transaction_scene(e, 8),
            Scene(
                2,
                "anomaly",
                "Anomaly Emerges",
                12,
                "Reveal unusual activity around the transaction.",
                "Cinematic financial-monitoring environment with "
                "transaction signals appearing around the focal event.",
                self._anomaly_visual(e),
                "Slow push-in followed by signal highlights.",
                ["transaction signal", "anomaly indicators", "risk pulse"],
                self._anomaly_overlays(e),
                self._anomaly_narration(e),
                "Signal sweep",
            ),
            self._risk_scene(e, 10),
            self._ai_scene(e, 12),
            self._decision_scene(e, 18),
        ]

    def _behavioural_investigation(
        self,
        e: Dict[str, Any],
    ) -> List[Scene]:
        """Story focused on customer behavioural risk."""

        return [
            self._transaction_scene(e, 8),
            Scene(
                2,
                "behaviour",
                "Behavioural Pattern",
                12,
                "Show how the transaction differs from expected customer behaviour.",
                "Abstract customer-behaviour timeline with normal activity "
                "and the current transaction separated visually.",
                self._behaviour_visual(e),
                "Camera travels along the behavioural timeline.",
                ["behaviour timeline", "normal baseline", "current event"],
                self._behaviour_overlays(e),
                self._behaviour_narration(e),
                "Timeline morph",
            ),
            self._risk_scene(e, 10),
            self._ai_scene(e, 10),
            self._decision_scene(e, 20),
        ]

    def _network_investigation(
        self,
        e: Dict[str, Any],
    ) -> List[Scene]:
        """Story focused on connected entities and graph context."""

        return [
            self._transaction_scene(e, 8),
            self._network_scene(e, 15),
            Scene(
                3,
                "graph_context",
                "Connected Risk Signals",
                12,
                "Explain why network evidence matters without confusing it "
                "with the overall AURA risk score.",
                "Large cinematic transaction network with connected nodes "
                "and selected high-risk relationships illuminated.",
                self._graph_context_visual(e),
                "Orbit around the focal customer node.",
                [
                    "customer node",
                    "transaction nodes",
                    "fraud connections",
                    "high-risk connections",
                ],
                self._graph_context_overlays(e),
                self._graph_context_narration(e),
                "Network dissolve",
            ),
            self._ai_scene(e, 13),
            self._decision_scene(e, 12),
        ]

    def _transaction_behaviour(
        self,
        e: Dict[str, Any],
    ) -> List[Scene]:
        """Story focused on transaction-level signals."""

        return [
            self._transaction_scene(e, 10),
            self._suspicion_scene(e, 12),
            self._risk_scene(e, 12),
            self._ai_scene(e, 12),
            self._decision_scene(e, 14),
        ]

    def _risk_review(
        self,
        e: Dict[str, Any],
    ) -> List[Scene]:
        """Short, executive-friendly risk review."""

        return [
            self._transaction_scene(e, 10),
            self._risk_scene(e, 15),
            self._ai_scene(e, 15),
            self._decision_scene(e, 20),
        ]

    # ------------------------------------------------------------------
    # Reusable scene builders
    # ------------------------------------------------------------------

    def _transaction_scene(
        self,
        e: Dict[str, Any],
        duration: int,
    ) -> Scene:
        amount = self._money(e.get("amount"))
        return Scene(
            1,
            "transaction",
            "The Transaction",
            duration,
            "Introduce the transaction and establish the investigation subject.",
            "Premium digital banking environment with a single transaction "
            "moving through a secure payment network.",
            "A transaction card materializes, the amount rises into focus, "
            "and the transaction ID appears subtly in the environment.",
            "Cinematic push-in toward the transaction card.",
            ["payment card", "transaction node", "secure network"],
            [
                f"TRANSACTION  {e['transaction_id']}",
                f"AMOUNT  {amount}",
            ],
            (
                f"AURA begins with a transaction of {amount}. "
                "The system now evaluates whether the activity fits "
                "the expected pattern."
            ),
            "Soft digital sweep",
        )

    def _suspicion_scene(
        self,
        e: Dict[str, Any],
        duration: int,
    ) -> Scene:
        reasons = e.get("investigation_reasons", [])
        return Scene(
            2,
            "suspicion",
            "Suspicious Activity Emerges",
            duration,
            "Reveal the deterministic evidence that triggered investigation.",
            "Financial-security command environment where risk signals "
            "appear around the transaction.",
            "Amount, velocity, anomaly, and novelty signals illuminate "
            "one after another.",
            "Tracking camera follows each signal before converging on the transaction.",
            [
                "amount signal",
                "velocity signal",
                "anomaly signal",
                "merchant novelty signal",
            ],
            self._suspicion_overlays(e, reasons),
            self._suspicion_narration(e, reasons),
            "Signal convergence",
        )

    def _risk_scene(
        self,
        e: Dict[str, Any],
        duration: int,
    ) -> Scene:
        return Scene(
            3,
            "risk_assessment",
            "AURA Risk Assessment",
            duration,
            "Present the final AURA risk assessment clearly.",
            "Elegant AURA risk environment with a large central risk score "
            "and supporting risk components.",
            f"The AURA score resolves to {self._score(e.get('risk_score'))}, "
            f"with a {e.get('risk_band', 'UNKNOWN')} classification.",
            "Slow circular camera movement around the central score.",
            ["AURA risk gauge", "risk band", "risk components"],
            [
                f"AURA RISK  {self._score(e.get('risk_score'))}",
                f"RISK BAND  {e.get('risk_band', 'UNKNOWN')}",
                f"BEHAVIOURAL RISK  {self._score(e.get('behavioural_risk_score'))}",
                f"ANOMALY RISK  {self._score(e.get('anomaly_risk'))}",
            ],
            (
                f"AURA combines the available risk signals into a final "
                f"assessment of {self._score(e.get('risk_score'))}, "
                f"classified as {e.get('risk_band', 'UNKNOWN')}."
            ),
            "Score reveal",
        )

    def _network_scene(
        self,
        e: Dict[str, Any],
        duration: int,
    ) -> Scene:
        return Scene(
            4,
            "network",
            "The Hidden Network",
            duration,
            "Reveal connected transaction and customer relationships.",
            "Deep 3D-inspired transaction network with the focal customer "
            "at the centre and connected activity surrounding it.",
            "Connections animate outward. Previously identified fraudulent "
            "and high-risk relationships become visible.",
            "Orbiting camera with depth parallax across the network.",
            [
                "customer node",
                "transaction nodes",
                "merchant relationship",
                "fraud connection",
                "high-risk connection",
            ],
            [
                f"GRAPH RISK  {self._score(e.get('graph_risk_score'))}",
                f"GRAPH BAND  {e.get('graph_risk_band', 'UNKNOWN')}",
                self._graph_metric_overlay(e, "transaction_count", "TRANSACTIONS"),
                self._graph_metric_overlay(
                    e,
                    "fraud_transaction_count",
                    "FRAUD TRANSACTIONS",
                ),
            ],
            (
                f"The network analysis produces a separate graph risk score "
                f"of {self._score(e.get('graph_risk_score'))}, "
                f"classified as {e.get('graph_risk_band', 'UNKNOWN')}. "
                "These network signals provide context for the investigation."
            ),
            "Network expansion",
        )

    def _ai_scene(
        self,
        e: Dict[str, Any],
        duration: int,
    ) -> Scene:
        return Scene(
            5,
            "ai_investigator",
            "AI Investigator",
            duration,
            "Show AURA's AI Investigator synthesising the evidence.",
            "Premium AI investigation workspace with evidence cards "
            "assembling into a coherent case narrative.",
            "Evidence cards converge into an AI-generated investigation "
            "assessment while the distinction between AURA risk and graph "
            "risk remains visually explicit.",
            "Gentle dolly-in with floating evidence layers.",
            ["AI investigator core", "evidence cards", "case narrative"],
            [
                f"AURA  {self._score(e.get('risk_score'))} "
                f"{e.get('risk_band', 'UNKNOWN')}",
                f"GRAPH  {self._score(e.get('graph_risk_score'))} "
                f"{e.get('graph_risk_band', 'UNKNOWN')}",
                f"ML FRAUD PROBABILITY  "
                f"{self._percentage(e.get('fraud_probability'))}",
            ],
            (
                "AURA's AI Investigator brings the evidence together. "
                "It keeps the final AURA risk assessment separate from "
                "the supporting network analysis."
            ),
            "Evidence fusion",
        )

    def _decision_scene(
        self,
        e: Dict[str, Any],
        duration: int,
    ) -> Scene:
        return Scene(
            6,
            "decision",
            "Investigation Decision",
            duration,
            "Close the story with the recommended operational decision.",
            "Executive-grade fraud operations environment with the "
            "investigation decision clearly isolated from the evidence.",
            "The investigation status resolves and the recommended action "
            "appears as the final operational outcome.",
            "Pull back from the decision into a wide command-centre view.",
            ["decision panel", "investigation status", "AURA logo"],
            [
                "INVESTIGATION FLAG  "
                + ("TRUE" if e.get("investigation_flag") else "FALSE"),
                f"ACTION  {e.get('recommended_action', 'REVIEW')}",
            ],
            (
                f"The investigation decision is "
                f"{e.get('recommended_action', 'REVIEW')}. "
                "AURA has transformed multiple signals into an actionable "
                "fraud-investigation outcome."
            ),
            "AURA logo fade",
        )

    # ------------------------------------------------------------------
    # Story-specific visual helpers
    # ------------------------------------------------------------------

    def _anomaly_visual(self, e: Dict[str, Any]) -> str:
        return (
            "A transaction pulse breaks away from the normal activity field; "
            f"the anomaly risk rises to {self._score(e.get('anomaly_risk'))}."
        )

    def _anomaly_overlays(self, e: Dict[str, Any]) -> List[str]:
        return [
            f"ANOMALY RISK  {self._score(e.get('anomaly_risk'))}",
            f"ANOMALY SCORE  {self._score(e.get('anomaly_score'))}",
        ]

    def _anomaly_narration(self, e: Dict[str, Any]) -> str:
        return (
            f"The transaction displays unusual activity, with an anomaly "
            f"risk of {self._score(e.get('anomaly_risk'))}."
        )

    def _behaviour_visual(self, e: Dict[str, Any]) -> str:
        return (
            "Normal customer activity forms a stable baseline while the "
            "current transaction visibly deviates from it."
        )

    def _behaviour_overlays(self, e: Dict[str, Any]) -> List[str]:
        return [
            f"BEHAVIOURAL RISK  {self._score(e.get('behavioural_risk_score'))}",
            f"AMOUNT RISK  {self._score(e.get('amount_risk'))}",
            f"VELOCITY RISK  {self._score(e.get('velocity_risk'))}",
            f"NOVELTY RISK  {self._score(e.get('novelty_risk'))}",
        ]

    def _behaviour_narration(self, e: Dict[str, Any]) -> str:
        return (
            f"Behavioural analysis assigns a risk score of "
            f"{self._score(e.get('behavioural_risk_score'))}, "
            "reflecting how the transaction differs from expected activity."
        )

    def _graph_context_visual(self, e: Dict[str, Any]) -> str:
        return (
            "The network expands to show connected entities while the "
            "focal transaction remains visually anchored at the centre."
        )

    def _graph_context_overlays(self, e: Dict[str, Any]) -> List[str]:
        return [
            f"GRAPH RISK  {self._score(e.get('graph_risk_score'))}",
            f"GRAPH BAND  {e.get('graph_risk_band', 'UNKNOWN')}",
        ]

    def _graph_context_narration(self, e: Dict[str, Any]) -> str:
        return (
            f"Network analysis shows a graph risk of "
            f"{self._score(e.get('graph_risk_score'))}, "
            f"classified as {e.get('graph_risk_band', 'UNKNOWN')}. "
            "The network evidence adds context rather than replacing "
            "the final AURA risk assessment."
        )

    def _suspicion_overlays(
        self,
        e: Dict[str, Any],
        reasons: List[Any],
    ) -> List[str]:
        overlays = [
            f"AMOUNT RISK  {self._score(e.get('amount_risk'))}",
            f"VELOCITY RISK  {self._score(e.get('velocity_risk'))}",
            f"ANOMALY RISK  {self._score(e.get('anomaly_risk'))}",
            f"NOVELTY RISK  {self._score(e.get('novelty_risk'))}",
        ]

        # Keep on-screen text concise. Full evidence remains available to
        # the renderer/application layer.
        if reasons:
            overlays.append(f"EVIDENCE  {str(reasons[0])[:80]}")

        return overlays

    def _suspicion_narration(
        self,
        e: Dict[str, Any],
        reasons: List[Any],
    ) -> str:
        if reasons:
            clean_reasons = [
                str(reason).strip().rstrip(".")
                for reason in reasons[:3]
                if str(reason).strip()
            ]

            if clean_reasons:
                if len(clean_reasons) == 1:
                    evidence_text = clean_reasons[0] + "."
                elif len(clean_reasons) == 2:
                    evidence_text = (
                        clean_reasons[0]
                        + ", and "
                        + clean_reasons[1]
                        + "."
                    )
                else:
                    evidence_text = (
                        ", ".join(clean_reasons[:-1])
                        + ", and "
                        + clean_reasons[-1]
                        + "."
                    )

                return (
                    "Multiple signals require attention. "
                    + evidence_text
                )

        return (
            "Multiple transaction-level signals require attention and "
            "move the event into investigation."
        )

    def _graph_metric_overlay(
        self,
        e: Dict[str, Any],
        key: str,
        label: str,
    ) -> str:
        value = e.get("graph_metrics", {}).get(key)
        if value is None:
            return f"{label}  N/A"
        return f"{label}  {value}"

    # ------------------------------------------------------------------
    # Formatting / fallback
    # ------------------------------------------------------------------

    def _fallback_story(
        self,
        investigation: Dict[str, Any],
    ) -> Dict[str, Any]:
        score = self._number(investigation.get("risk_score"))

        if score is not None and score >= 80:
            story_type = "full_investigation"
        elif score is not None and score >= 60:
            story_type = "full_investigation"
        elif score is not None and score < 30:
            story_type = "risk_review"
        else:
            story_type = "transaction_behaviour"

        return {
            "story_type": story_type,
            "title": self._video_title(story_type),
            "selection_mode": "AUTO",
        }

    def _video_title(self, story_type: str) -> str:
        titles = {
            "full_investigation": "AURA AI Fraud Investigation",
            "anomaly_investigation": "AURA Anomaly Investigation",
            "behavioural_investigation": "AURA Behavioural Risk Investigation",
            "network_investigation": "AURA Network Investigation",
            "transaction_behaviour": "AURA Transaction Behaviour Review",
            "risk_review": "AURA Risk Review",
        }
        return titles.get(
            story_type,
            "AURA AI Fraud Investigation",
        )

    @staticmethod
    def _number(value: Any) -> Optional[float]:
        if value is None:
            return None

        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        return round(number, 6)

    @staticmethod
    def _score(value: Any) -> str:
        if value is None:
            return "N/A"

        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _percentage(value: Any) -> str:
        if value is None:
            return "N/A"

        try:
            number = float(value)
            # InvestigationEngine stores fraud_probability as 0.0–1.0.
            if 0 <= number <= 1:
                number *= 100
            return f"{number:.2f}%"
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _money(value: Any) -> str:
        if value is None:
            return "N/A"

        try:
            return f"${float(value):,.2f}"
        except (TypeError, ValueError):
            return str(value)


# Convenience function for simple callers.
def generate_scenes(
    investigation_result: Dict[str, Any],
    selected_story: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate an AURA scene plan without instantiating SceneGenerator."""
    return SceneGenerator().generate(
        investigation_result,
        selected_story,
    )
