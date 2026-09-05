"""
AURA AI Video Generator
-----------------------

Generates cinematic investigation video clips using
xAI Grok Imagine Video.

This module is intentionally kept separate from:
- fraud detection
- investigation logic
- story selection
- dashboard
- action routing

It acts as the AI-video provider layer.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import xai_sdk


class AIVideoGenerationError(RuntimeError):
    """Raised when AI video generation fails."""


class AIVideoGenerator:
    """
    Provider wrapper for xAI Grok Imagine Video.
    """

    MODEL = "grok-imagine-video-1.5"

    def __init__(
        self,
        api_key: Optional[str] = None,
        output_dir: str = "data/video/ai_generated",
    ) -> None:
        load_dotenv()

        self.api_key = api_key or os.getenv("XAI_API_KEY")

        if not self.api_key:
            raise AIVideoGenerationError(
                "XAI_API_KEY was not found in the environment."
            )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.client = xai_sdk.Client(api_key=self.api_key)

    def generate_clip(
        self,
        prompt: str,
        duration: int = 8,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        filename: str = "aura_scene.mp4",
        generate_audio: bool = False,
    ) -> dict:
        """
        Generate one AI video clip.

        Parameters
        ----------
        prompt:
            Cinematic generation prompt.

        duration:
            Clip duration in seconds.

        aspect_ratio:
            Target aspect ratio.

        resolution:
            Video resolution.

        filename:
            Local output filename.

        generate_audio:
            Whether Grok should generate an audio track.

        Returns
        -------
        dict
            Metadata about the generated clip.
        """

        if not prompt or not prompt.strip():
            raise ValueError("Video prompt cannot be empty.")

        if duration < 1 or duration > 15:
            raise ValueError(
                "Grok Imagine Video currently supports "
                "durations between 1 and 15 seconds."
            )

        try:
            print()
            print("=" * 70)
            print("AURA AI VIDEO GENERATION")
            print("=" * 70)
            print(f"MODEL:      {self.MODEL}")
            print(f"DURATION:   {duration}s")
            print(f"ASPECT:     {aspect_ratio}")
            print(f"RESOLUTION: {resolution}")
            print(f"AUDIO:      {generate_audio}")
            print()
            print("PROMPT:")
            print(prompt)
            print()
            print("Generating video...")
            print("This may take several minutes.")
            print()

            response = self.client.video.generate(
                prompt=prompt,
                model=self.MODEL,
                duration=duration,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                generate_audio=generate_audio,
            )

            video_url = response.url

            if not video_url:
                raise AIVideoGenerationError(
                    "xAI returned no video URL."
                )

            output_path = self.output_dir / filename

            self._download_video(
                video_url=video_url,
                output_path=output_path,
            )

            result = {
                "success": True,
                "model": self.MODEL,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "video_url": video_url,
                "local_path": str(output_path),
            }

            if hasattr(response, "cost_usd"):
                result["cost_usd"] = response.cost_usd

            print("=" * 70)
            print("VIDEO GENERATION COMPLETE")
            print("=" * 70)
            print(f"OUTPUT: {output_path}")

            if "cost_usd" in result:
                print(f"COST:   ${result['cost_usd']:.4f}")

            print("=" * 70)

            return result

        except Exception as exc:
            raise AIVideoGenerationError(
                f"xAI video generation failed: {exc}"
            ) from exc

    @staticmethod
    def _download_video(
        video_url: str,
        output_path: Path,
    ) -> None:
        """
        Download generated video to the local AURA project.
        """

        import requests

        response = requests.get(
            video_url,
            timeout=300,
        )

        response.raise_for_status()

        output_path.write_bytes(response.content)


def generate_ai_video(
    prompt: str,
    duration: int = 8,
    filename: str = "aura_scene.mp4",
) -> dict:
    """
    Convenience function for generating a video clip.
    """

    generator = AIVideoGenerator()

    return generator.generate_clip(
        prompt=prompt,
        duration=duration,
        filename=filename,
    )