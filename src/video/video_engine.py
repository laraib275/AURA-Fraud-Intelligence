"""
AURA Video Engine
-----------------

Main orchestration layer for AURA video intelligence.

Flow:

User Request
    ↓
Video Intent Engine
    ↓
Story Selection
    ↓
Scene Generation
    ↓
Structured Video Plan

This module creates the video plan.
Actual AI video generation is intentionally kept separate.
"""

from __future__ import annotations

from typing import Any, Dict

from src.video.intent.video_intent_engine import VideoIntentEngine
from src.video.scene_generator import SceneGenerator
from src.video.story_selector import DynamicStorySelector


class VideoEngine:
    """Orchestrates AURA's video intelligence workflow."""

    def __init__(self) -> None:
        self.intent_engine = VideoIntentEngine()
        self.story_selector = DynamicStorySelector()
        self.scene_generator = SceneGenerator()

    def create_video_plan(
        self,
        request: str,
        investigation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert a natural-language request and investigation result
        into a structured video plan.
        """

        if not isinstance(request, str):
            raise TypeError("Video request must be a string.")

        if not request.strip():
            raise ValueError("Video request cannot be empty.")

        if not isinstance(investigation_result, dict):
            raise TypeError("Investigation result must be a dictionary.")

        # ----------------------------------------------------------
        # 1. Understand the user's request
        # ----------------------------------------------------------

        intent = self.intent_engine.classify(request)

        intent_data = intent.to_dict()

        # ----------------------------------------------------------
        # 2. Select the appropriate story
        # ----------------------------------------------------------

        selected_story = self._select_story(
            intent=intent,
            investigation_result=investigation_result,
        )

        # ----------------------------------------------------------
        # 3. Generate scenes
        # ----------------------------------------------------------

        scene_plan = self.scene_generator.generate(
            investigation_result=investigation_result,
            selected_story=selected_story,
        )

        # ----------------------------------------------------------
        # 4. Attach intent/presentation metadata
        # ----------------------------------------------------------

        scene_plan["requested_intent"] = intent_data
        scene_plan["audience"] = intent.audience
        scene_plan["requested_duration_seconds"] = intent.duration_seconds
        scene_plan["requested_visual_style"] = intent.visual_style
        scene_plan["intent_confidence"] = intent.confidence

        # The current engine is a planning layer.
        scene_plan["generation_mode"] = "PLAN_ONLY"

        # ----------------------------------------------------------
        # 5. Return complete plan
        # ----------------------------------------------------------

        return {
            "success": True,
            "request": request,
            "intent": intent_data,
            "selected_story": selected_story,
            "video_plan": scene_plan,
        }

    def _select_story(
        self,
        intent: Any,
        investigation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Translate content intent into an existing story type.

        Executive summary currently uses the existing full-investigation
        scene architecture while preserving executive-summary intent
        metadata. A dedicated executive storyboard can be added later.
        """

        intent_to_story = {
            "full_investigation": "full_investigation",
            "executive_summary": "full_investigation",
            "risk_explanation": "risk_review",
            "network_investigation": "network_investigation",
            "behavioural_explanation": "behavioural_investigation",
            "anomaly_explanation": "anomaly_investigation",
            "training": "full_investigation",
        }

        requested_story_type = intent_to_story.get(
            intent.content_intent,
            "full_investigation",
        )

        # ----------------------------------------------------------
        # Let the existing Story Selector analyse the evidence.
        # We do not duplicate risk-selection logic here.
        # ----------------------------------------------------------

        try:
            selection_result = self.story_selector.select(
                investigation_result
            )
        except TypeError:
            selection_result = self.story_selector.select(
                investigation_result=investigation_result
            )

        if isinstance(selection_result, dict):
            if "selected_story" in selection_result:
                auto_story = selection_result["selected_story"]
            else:
                auto_story = selection_result
        else:
            auto_story = {}

        if not isinstance(auto_story, dict):
            auto_story = {}

        story = dict(auto_story)

        # User's content intent takes precedence over automatic
        # evidence-driven story selection.
        story["story_type"] = requested_story_type
        story["selection_mode"] = "INTENT"
        story["intent_content"] = intent.content_intent
        story["intent_audience"] = intent.audience

        return story

    def plan_from_investigation(
        self,
        request: str,
        investigation_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Alias for external/API integration."""

        return self.create_video_plan(
            request=request,
            investigation_result=investigation_result,
        )


def create_video_plan(
    request: str,
    investigation_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Convenience function for external callers."""

    engine = VideoEngine()

    return engine.create_video_plan(
        request=request,
        investigation_result=investigation_result,
    )


if __name__ == "__main__":
    print("=" * 80)
    print("AURA VIDEO ENGINE")
    print("=" * 80)
    print()
    print("Video Engine loaded successfully.")
    print("Mode: PLAN_ONLY")
    print()
    print("Pipeline:")
    print("  User Request")
    print("      ↓")
    print("  Video Intent Engine")
    print("      ↓")
    print("  Story Selector")
    print("      ↓")
    print("  Scene Generator")
    print("      ↓")
    print("  Structured Video Plan")
    print()
    print("=" * 80)