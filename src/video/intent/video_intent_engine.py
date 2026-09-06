"""
AURA Video Intent Engine

Determines:
1. What the requested video is about
2. Who the video is for
3. How the video should be presented

This module does NOT generate video.
It creates structured instructions for the downstream
Story Selector and Scene Generator.
"""

from dataclasses import asdict, dataclass
from typing import Dict, List


@dataclass
class VideoIntent:
    """Structured representation of a video request."""

    content_intent: str
    audience: str
    duration_seconds: int
    visual_style: str
    confidence: float
    explanation: str

    def to_dict(self) -> Dict:
        return asdict(self)


class VideoIntentEngine:
    """
    Deterministic natural-language video intent engine.

    Content and audience are intentionally separated so that
    AURA can support combinations such as:

        Network investigation + CEO audience
        Risk explanation + Analyst audience
        Behaviour explanation + General audience
    """

    CONTENT_DEFINITIONS = {
        "full_investigation": {
            "duration": 60,
            "style": "premium cinematic 2.5D investigation",
        },
        "executive_summary": {
            "duration": 45,
            "style": "premium executive cinematic briefing",
        },
        "risk_explanation": {
            "duration": 45,
            "style": "premium cinematic risk explanation",
        },
        "network_investigation": {
            "duration": 50,
            "style": "cinematic financial network visualization",
        },
        "behavioural_explanation": {
            "duration": 50,
            "style": "cinematic behavioural intelligence",
        },
        "anomaly_explanation": {
            "duration": 45,
            "style": "cinematic anomaly detection",
        },
        "training": {
            "duration": 90,
            "style": "professional cinematic training",
        },
    }

    AUDIENCE_DEFINITIONS = {
        "general": "general",
        "analyst": "fraud analyst",
        "executive": "CEO / executive",
        "trainee": "fraud analyst / trainee",
    }

    CONTENT_KEYWORDS = {
        "network_investigation": [
            "network",
            "networks",
            "connection",
            "connections",
            "connected activity",
            "connected transactions",
            "transaction network",
            "relationship",
            "relationships",
            "graph",
            "trace the network",
            "show the network",
            "show the connections",
        ],
        "behavioural_explanation": [
            "behaviour",
            "behavior",
            "behavioural",
            "behavioral",
            "customer behaviour",
            "customer behavior",
            "customer pattern",
            "spending pattern",
            "activity pattern",
            "behaviour pattern",
            "behavior pattern",
        ],
        "anomaly_explanation": [
            "anomaly",
            "anomalies",
            "outlier",
            "outliers",
            "deviation",
            "abnormal activity",
            "unusual activity",
            "unusual transaction",
        ],
        "risk_explanation": [
            "risk",
            "risk score",
            "risk assessment",
            "critical",
            "high risk",
            "high-risk",
            "medium risk",
            "medium-risk",
            "low risk",
            "low-risk",
            "why critical",
            "why high risk",
            "why risky",
            "explain the risk",
            "explain why",
            "why was this flagged",
            "why this was flagged",
            "why is this flagged",
            "why was it flagged",
            "why is this critical",
            "why is this high risk",
            "explain this transaction",
        ],
        "training": [
            "training",
            "train analysts",
            "train an analyst",
            "teach analysts",
            "teach an analyst",
            "educational",
            "lesson",
            "tutorial",
            "teach me",
            "how does aura work",
            "how aura works",
        ],
        "executive_summary": [
            "executive summary",
            "executive briefing",
            "management briefing",
            "ceo summary",
            "ceo briefing",
            "board summary",
            "leadership summary",
            "briefing summary",
            "executive overview",
        ],
        "full_investigation": [
            "investigation",
            "investigate",
            "fraud investigation",
            "fraud case",
            "case investigation",
            "full investigation",
            "complete investigation",
            "investigation story",
            "what happened",
            "tell the story",
            "story behind",
        ],
    }

    AUDIENCE_KEYWORDS = {
        "executive": [
            "ceo",
            "chief executive",
            "executive",
            "board",
            "management",
            "leadership",
            "senior management",
            "for the ceo",
            "for management",
            "executive audience",
        ],
        "analyst": [
            "analyst",
            "fraud analyst",
            "investigator",
            "investigators",
            "fraud team",
            "investigation team",
        ],
        "trainee": [
            "trainee",
            "new analyst",
            "new analysts",
            "learn",
            "students",
        ],
    }

    def classify(self, request: str) -> VideoIntent:
        """Classify a natural-language video request."""

        if not isinstance(request, str):
            raise TypeError("Video request must be a string.")

        text = request.strip().lower()

        if not text:
            return self._default_intent(
                "No specific video request was provided."
            )

        audience, audience_matches = self._detect_audience(text)

        content_scores = self._score_content(text)

        best_content = self._select_content_intent(
            content_scores,
            audience,
        )

        confidence = self._calculate_confidence(
            content_scores,
            best_content,
        )

        definition = self.CONTENT_DEFINITIONS[best_content]

        visual_style = definition["style"]

        # Adapt presentation style to audience without changing
        # the underlying content intent.
        if audience == "executive":
            visual_style = (
                "premium executive cinematic "
                + self._style_topic(best_content)
            )

        elif audience == "analyst":
            visual_style = (
                "professional cinematic analyst "
                + self._style_topic(best_content)
            )

        elif audience == "trainee":
            visual_style = (
                "professional cinematic training "
                + self._style_topic(best_content)
            )

        explanation_parts = []

        content_matches = content_scores[best_content]["matched"]

        if content_matches:
            explanation_parts.append(
                f"Content detected from: {', '.join(content_matches)}."
            )

        if audience_matches:
            explanation_parts.append(
                f"Audience detected from: {', '.join(audience_matches)}."
            )

        explanation = " ".join(explanation_parts)

        if not explanation:
            explanation = (
                "No specific intent detected; using a full investigation story."
            )

        return VideoIntent(
            content_intent=best_content,
            audience=self.AUDIENCE_DEFINITIONS[audience],
            duration_seconds=definition["duration"],
            visual_style=visual_style,
            confidence=confidence,
            explanation=explanation,
        )

    def _score_content(self, text: str) -> Dict[str, Dict]:
        """Score possible content intents."""

        results = {}

        for intent, keywords in self.CONTENT_KEYWORDS.items():

            matched: List[str] = []

            for keyword in keywords:
                if keyword in text:
                    matched.append(keyword)

            score = 0

            for keyword in matched:
                # Multi-word phrases are more specific.
                if " " in keyword or "-" in keyword:
                    score += 2
                else:
                    score += 1

            results[intent] = {
                "score": score,
                "matched": matched,
            }

        return results

    def _detect_audience(self, text: str):
        """Detect intended audience independently from content."""

        scores = {}

        for audience, keywords in self.AUDIENCE_KEYWORDS.items():

            matched = []

            for keyword in keywords:
                if keyword in text:
                    matched.append(keyword)

            score = 0

            for keyword in matched:
                if " " in keyword:
                    score += 2
                else:
                    score += 1

            scores[audience] = {
                "score": score,
                "matched": matched,
            }

        best = max(
            scores,
            key=lambda audience: scores[audience]["score"]
        )

        if scores[best]["score"] == 0:
            return "general", []

        return best, scores[best]["matched"]

    def _select_content_intent(
        self,
        scores: Dict[str, Dict],
        audience: str,
    ) -> str:
        """
        Select the content intent.

        Explicit audience requests such as "CEO briefing" should
        not accidentally turn a fraud case into full_investigation.
        The audience remains separate from the content.
        """

        # Strong phrase-level decisions.
        if scores["executive_summary"]["score"] >= 2:
            return "executive_summary"

        if scores["network_investigation"]["score"] >= 2:
            return "network_investigation"

        if scores["behavioural_explanation"]["score"] >= 2:
            return "behavioural_explanation"

        if scores["risk_explanation"]["score"] >= 2:
            return "risk_explanation"

        if scores["training"]["score"] >= 2:
            return "training"

        if scores["anomaly_explanation"]["score"] >= 2:
            return "anomaly_explanation"

        # Explicit investigation language.
        if scores["full_investigation"]["score"] >= 2:
            return "full_investigation"

        # Single-word fallback scoring.
        best = max(
            scores,
            key=lambda intent: scores[intent]["score"]
        )

        if scores[best]["score"] > 0:
            return best

        return "full_investigation"

    def _calculate_confidence(
        self,
        scores: Dict[str, Dict],
        best_intent: str,
    ) -> float:
        """Calculate deterministic confidence."""

        best_score = scores[best_intent]["score"]

        other_scores = [
            data["score"]
            for intent, data in scores.items()
            if intent != best_intent
        ]

        second_score = max(other_scores) if other_scores else 0

        if best_score >= 4 and best_score > second_score:
            return 0.99

        if best_score >= 3 and best_score > second_score:
            return 0.98

        if best_score >= 2 and best_score > second_score:
            return 0.95

        if best_score > second_score:
            return 0.90

        if best_score > 0:
            return 0.80

        return 0.70

    def _style_topic(self, content_intent: str) -> str:
        """Return a short style description for audience adaptation."""

        topics = {
            "full_investigation": "investigation",
            "executive_summary": "executive briefing",
            "risk_explanation": "risk explanation",
            "network_investigation": "financial network investigation",
            "behavioural_explanation": "behavioural intelligence",
            "anomaly_explanation": "anomaly investigation",
            "training": "fraud intelligence training",
        }

        return topics.get(content_intent, "investigation")

    def _default_intent(self, explanation: str) -> VideoIntent:
        """Return safe default."""

        return VideoIntent(
            content_intent="full_investigation",
            audience="general",
            duration_seconds=60,
            visual_style="premium cinematic 2.5D investigation",
            confidence=0.70,
            explanation=explanation,
        )


def classify_video_request(request: str) -> Dict:
    """Convenience function for external callers."""

    engine = VideoIntentEngine()

    return engine.classify(request).to_dict()


if __name__ == "__main__":

    engine = VideoIntentEngine()

    test_requests = [
        "Create a video explaining why this transaction is critical",
        "Create a video showing the suspicious network connections",
        "Create a CEO briefing about this fraud case",
        "Create a video explaining the customer's unusual behaviour",
        "Create a video explaining the anomaly",
        "Create a training video for fraud analysts",
        "Create a full investigation video",
        "Create an executive summary video",
        "Why was this transaction flagged?",
        "Create a management briefing about this case",
        "Create a CEO video showing the suspicious network",
        "Create an analyst video explaining the critical risk",
    ]

    print("=" * 75)
    print("AURA VIDEO INTENT ENGINE TEST")
    print("=" * 75)

    for request in test_requests:

        result = engine.classify(request)

        print()
        print(f"REQUEST: {request}")
        print(f"CONTENT: {result.content_intent}")
        print(f"AUDIENCE: {result.audience}")
        print(f"DURATION: {result.duration_seconds}s")
        print(f"STYLE: {result.visual_style}")
        print(f"CONFIDENCE: {result.confidence}")
        print(f"EXPLANATION: {result.explanation}")