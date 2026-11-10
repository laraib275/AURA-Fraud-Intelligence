from __future__ import annotations

import math
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont


class VideoRenderer:
    """
    AURA Video Renderer

    Converts SceneGenerator output into cinematic scene assets.

    Responsibilities:
    - Render individual scenes as image sequences
    - Create AURA's premium pink visual identity
    - Animate risk scores, transaction data, signals and networks
    - Prepare scene assets for FFmpeg/video assembly

    This module does NOT perform fraud detection.
    It only visualizes evidence produced by the investigation pipeline.
    """

    WIDTH = 1920
    HEIGHT = 1080
    FPS = 30

    PINK = (219, 39, 119)
    PINK_SOFT = (253, 242, 248)
    WHITE = (255, 255, 255)
    BLACK = (24, 24, 27)
    GREY = (107, 114, 128)
    LIGHT_GREY = (229, 231, 235)
    DARK_GREY = (55, 65, 81)
    RED = (220, 38, 38)
    GREEN = (22, 163, 74)
    AMBER = (217, 119, 6)

    def __init__(
        self,
        output_dir: str = "data/video",
        width: int = WIDTH,
        height: int = HEIGHT,
        fps: int = FPS,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.width = width
        self.height = height
        self.fps = fps

        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.font_regular = self._load_font(32)
        self.font_small = self._load_font(24)
        self.font_medium = self._load_font(40)
        self.font_large = self._load_font(72)
        self.font_huge = self._load_font(120)

    # ------------------------------------------------------------------
    # FONT
    # ------------------------------------------------------------------

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """
        Load a commonly available Windows font.
        Falls back to Pillow's default font if unavailable.
        """

        candidates = [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
        ]

        for font_path in candidates:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    pass

        return ImageFont.load_default()

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def render(
        self,
        video_data: Dict[str, Any],
        output_name: str = "aura_investigation",
    ) -> Dict[str, Any]:
        """
        Render all scenes from SceneGenerator output.

        Returns metadata describing generated assets.
        """

        scenes = video_data.get("scenes", [])

        if not scenes:
            raise ValueError("Video data contains no scenes.")

        evidence = video_data.get("evidence_summary", {})

        output_path = self.output_dir / output_name
        output_path.mkdir(parents=True, exist_ok=True)

        rendered_scenes: List[Dict[str, Any]] = []

        for index, scene in enumerate(scenes, start=1):
            scene_dir = output_path / f"scene_{index:02d}"
            scene_dir.mkdir(parents=True, exist_ok=True)

            frames = self.render_scene(
                scene=scene,
                evidence=evidence,
                output_dir=scene_dir,
            )

            rendered_scenes.append(
                {
                    "scene_number": index,
                    "title": scene.get("title", f"Scene {index}"),
                    "duration_seconds": scene.get("duration_seconds", 5),
                    "frame_count": len(frames),
                    "frame_directory": str(scene_dir),
                }
            )

        return {
            "video_title": video_data.get(
                "video_title",
                "AURA AI Fraud Investigation",
            ),
            "story_type": video_data.get("story_type"),
            "duration_seconds": video_data.get("duration_seconds"),
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "output_directory": str(output_path),
            "scenes": rendered_scenes,
        }

    # ------------------------------------------------------------------
    # SCENE RENDERING
    # ------------------------------------------------------------------

    def render_scene(
        self,
        scene: Dict[str, Any],
        evidence: Dict[str, Any],
        output_dir: Path,
    ) -> List[str]:
        """
        Render one scene into PNG frames.
        """

        duration = float(scene.get("duration_seconds", scene.get("duration", 5)))
        frame_count = max(1, int(duration * self.fps))

        scene_type = str(scene.get("scene_type", "")).lower()

        frames: List[str] = []

        for frame_index in range(frame_count):
            progress = (
                frame_index / max(frame_count - 1, 1)
            )

            image = self._create_background(progress)

            if scene_type in {"transaction", "opening"}:
                self._draw_transaction_scene(
                    image,
                    scene,
                    evidence,
                    progress,
                )

            elif scene_type in {"signals", "anomaly"}:
                self._draw_signal_scene(
                    image,
                    scene,
                    evidence,
                    progress,
                )

            elif scene_type in {"risk", "risk_assessment"}:
                self._draw_risk_scene(
                    image,
                    scene,
                    evidence,
                    progress,
                )

            elif scene_type in {"network", "graph"}:
                self._draw_network_scene(
                    image,
                    scene,
                    evidence,
                    progress,
                )

            elif scene_type in {"ai", "investigator"}:
                self._draw_ai_scene(
                    image,
                    scene,
                    evidence,
                    progress,
                )

            elif scene_type in {"decision", "conclusion"}:
                self._draw_decision_scene(
                    image,
                    scene,
                    evidence,
                    progress,
                )

            else:
                self._draw_generic_scene(
                    image,
                    scene,
                    evidence,
                    progress,
                )

            self._draw_branding(image)

            frame_path = output_dir / f"frame_{frame_index:05d}.png"
            image.save(frame_path)

            frames.append(str(frame_path))

        return frames

    # ------------------------------------------------------------------
    # BACKGROUND
    # ------------------------------------------------------------------

    def _create_background(self, progress: float) -> Image.Image:
        """
        Create a premium light AURA background.
        """

        image = Image.new(
            "RGB",
            (self.width, self.height),
            self.PINK_SOFT,
        )

        draw = ImageDraw.Draw(image)

        # Soft radial-style layers.
        max_radius = 700

        for i in range(10):
            radius = int(max_radius * (1 - i / 12))

            alpha_factor = 0.025 + (
                0.02 * math.sin(progress * math.pi)
            )

            pink = tuple(
                int(
                    self.PINK[channel] * alpha_factor
                    + self.PINK_SOFT[channel] * (1 - alpha_factor)
                )
                for channel in range(3)
            )

            draw.ellipse(
                (
                    self.width - radius,
                    -radius // 3,
                    self.width + radius,
                    radius * 2,
                ),
                fill=pink,
            )

        # Subtle bottom panel.
        draw.rectangle(
            (0, self.height - 130, self.width, self.height),
            fill=(255, 255, 255),
        )

        return image

    # ------------------------------------------------------------------
    # SCENE 1
    # ------------------------------------------------------------------

    def _draw_transaction_scene(
        self,
        image: Image.Image,
        scene: Dict[str, Any],
        evidence: Dict[str, Any],
        progress: float,
    ) -> None:

        draw = ImageDraw.Draw(image)

        self._draw_title(
            draw,
            scene.get("title", "The Transaction"),
        )

        transaction_id = evidence.get(
            "transaction_id",
            "UNKNOWN",
        )

        amount = evidence.get(
            "amount",
            evidence.get("transaction_amount", "—"),
        )

        self._draw_card(
            draw,
            250,
            330,
            1670,
            760,
        )

        draw.text(
            (330, 400),
            "TRANSACTION",
            font=self.font_small,
            fill=self.GREY,
        )

        draw.text(
            (330, 455),
            str(transaction_id),
            font=self.font_medium,
            fill=self.BLACK,
        )

        draw.text(
            (330, 560),
            "Transaction Amount",
            font=self.font_small,
            fill=self.GREY,
        )

        draw.text(
            (330, 610),
            self._format_amount(amount),
            font=self.font_large,
            fill=self.PINK,
        )

        # Animated signal pulse.
        pulse = int(20 + 15 * math.sin(progress * math.pi * 4))

        draw.ellipse(
            (
                1450 - pulse,
                490 - pulse,
                1550 + pulse,
                590 + pulse,
            ),
            outline=self.PINK,
            width=5,
        )

        draw.ellipse(
            (1450, 490, 1550, 590),
            fill=self.PINK,
        )

        self._center_text(
            draw,
            "AURA",
            1500,
            535,
            self.font_medium,
            self.WHITE,
        )

    # ------------------------------------------------------------------
    # SCENE 2
    # ------------------------------------------------------------------

    def _draw_signal_scene(
        self,
        image: Image.Image,
        scene: Dict[str, Any],
        evidence: Dict[str, Any],
        progress: float,
    ) -> None:

        draw = ImageDraw.Draw(image)

        self._draw_title(
            draw,
            scene.get(
                "title",
                "Suspicious Activity Emerges",
            ),
        )

        reasons = evidence.get(
            "investigation_reasons",
            [],
        )

        if not reasons:
            reasons = [
                "Multiple behavioural signals detected",
                "Unusual transaction characteristics",
                "Transaction requires investigation",
            ]

        y = 330

        for index, reason in enumerate(reasons[:3]):

            offset = int(
                max(0, 80 * (progress * 3 - index))
            )

            x = 300 - offset

            self._draw_card(
                draw,
                x,
                y,
                1620,
                y + 150,
            )

            draw.ellipse(
                (350, y + 50, 410, y + 110),
                fill=self.PINK,
            )

            draw.text(
                (450, y + 48),
                self._clean_text(reason),
                font=self.font_regular,
                fill=self.BLACK,
            )

            y += 190

    # ------------------------------------------------------------------
    # SCENE 3
    # ------------------------------------------------------------------

    def _draw_risk_scene(
        self,
        image: Image.Image,
        scene: Dict[str, Any],
        evidence: Dict[str, Any],
        progress: float,
    ) -> None:

        draw = ImageDraw.Draw(image)

        self._draw_title(
            draw,
            scene.get(
                "title",
                "AURA Risk Assessment",
            ),
        )

        score = float(
            evidence.get("risk_score", 0)
        )

        band = str(
            evidence.get(
                "risk_band",
                "UNKNOWN",
            )
        ).upper()

        animated_score = score * min(
            progress * 1.5,
            1.0,
        )

        self._draw_card(
            draw,
            350,
            300,
            1570,
            850,
        )

        self._center_text(
            draw,
            f"{animated_score:.2f}",
            960,
            520,
            self.font_huge,
            self.PINK,
        )

        self._center_text(
            draw,
            f"AURA RISK • {band}",
            960,
            680,
            self.font_large,
            self.RED if band == "CRITICAL" else self.AMBER,
        )

        self._center_text(
            draw,
            "Behavioural + anomaly intelligence",
            960,
            790,
            self.font_regular,
            self.GREY,
        )

    # ------------------------------------------------------------------
    # SCENE 4
    # ------------------------------------------------------------------

    def _draw_network_scene(
        self,
        image: Image.Image,
        scene: Dict[str, Any],
        evidence: Dict[str, Any],
        progress: float,
    ) -> None:

        draw = ImageDraw.Draw(image)

        self._draw_title(
            draw,
            scene.get(
                "title",
                "The Hidden Network",
            ),
        )

        center_x = 960
        center_y = 590

        nodes = [
            (center_x, center_y),
            (600, 430),
            (1320, 430),
            (560, 760),
            (1360, 760),
            (960, 330),
        ]

        # Animated network lines.
        for node_x, node_y in nodes[1:]:
            draw.line(
                (
                    center_x,
                    center_y,
                    node_x,
                    node_y,
                ),
                fill=self.PINK,
                width=5,
            )

        # Nodes.
        for index, (x, y) in enumerate(nodes):

            radius = 48

            if index == 0:
                radius = 70

            draw.ellipse(
                (
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                ),
                fill=self.PINK
                if index == 0
                else self.WHITE,
                outline=self.PINK,
                width=5,
            )

            if index == 0:
                self._center_text(
                    draw,
                    "TX",
                    x,
                    y,
                    self.font_small,
                    self.WHITE,
                )

        graph_score = evidence.get(
            "graph_risk_score",
            "—",
        )

        graph_band = evidence.get(
            "graph_risk_band",
            "UNKNOWN",
        )

        self._draw_card(
            draw,
            690,
            850,
            1230,
            990,
        )

        draw.text(
            (740, 890),
            f"GRAPH RISK  {graph_score}  •  {graph_band}",
            font=self.font_medium,
            fill=self.BLACK,
        )

    # ------------------------------------------------------------------
    # SCENE 5
    # ------------------------------------------------------------------

    def _draw_ai_scene(
        self,
        image: Image.Image,
        scene: Dict[str, Any],
        evidence: Dict[str, Any],
        progress: float,
    ) -> None:

        draw = ImageDraw.Draw(image)

        self._draw_title(
            draw,
            scene.get(
                "title",
                "AI Investigator",
            ),
        )

        # Digital AURA investigator.
        cx = 960
        cy = 540

        pulse = int(
            10 + 8 * math.sin(progress * math.pi * 4)
        )

        draw.ellipse(
            (
                cx - 180 - pulse,
                cy - 180 - pulse,
                cx + 180 + pulse,
                cy + 180 + pulse,
            ),
            outline=self.PINK,
            width=6,
        )

        draw.ellipse(
            (
                cx - 130,
                cy - 130,
                cx + 130,
                cy + 130,
            ),
            fill=self.PINK,
        )

        self._center_text(
            draw,
            "AURA",
            cx,
            cy - 15,
            self.font_large,
            self.WHITE,
        )

        self._center_text(
            draw,
            "AI INVESTIGATOR",
            cx,
            cy + 80,
            self.font_small,
            self.WHITE,
        )

        # Evidence cards.
        cards = [
            "Transaction evidence",
            "Behavioural evidence",
            "Network context",
        ]

        y = 330

        for card in cards:
            self._draw_card(
                draw,
                250,
                y,
                650,
                y + 110,
            )

            draw.text(
                (300, y + 35),
                card,
                font=self.font_regular,
                fill=self.BLACK,
            )

            y += 150

    # ------------------------------------------------------------------
    # SCENE 6
    # ------------------------------------------------------------------

    def _draw_decision_scene(
        self,
        image: Image.Image,
        scene: Dict[str, Any],
        evidence: Dict[str, Any],
        progress: float,
    ) -> None:

        draw = ImageDraw.Draw(image)

        self._draw_title(
            draw,
            scene.get(
                "title",
                "Investigation Decision",
            ),
        )

        band = str(
            evidence.get(
                "risk_band",
                "UNKNOWN",
            )
        ).upper()

        score = evidence.get(
            "risk_score",
            "—",
        )

        action = evidence.get(
            "recommended_action",
            "IMMEDIATE INVESTIGATION",
        )

        self._draw_card(
            draw,
            350,
            300,
            1570,
            850,
        )

        self._center_text(
            draw,
            f"{score}",
            960,
            470,
            self.font_huge,
            self.PINK,
        )

        self._center_text(
            draw,
            band,
            960,
            630,
            self.font_large,
            self.RED if band == "CRITICAL" else self.AMBER,
        )

        self._center_text(
            draw,
            str(action),
            960,
            760,
            self.font_medium,
            self.BLACK,
        )

        self._center_text(
            draw,
            "Human investigation required",
            960,
            850,
            self.font_regular,
            self.GREY,
        )

    # ------------------------------------------------------------------
    # GENERIC
    # ------------------------------------------------------------------

    def _draw_generic_scene(
        self,
        image: Image.Image,
        scene: Dict[str, Any],
        evidence: Dict[str, Any],
        progress: float,
    ) -> None:

        draw = ImageDraw.Draw(image)

        self._draw_title(
            draw,
            scene.get("title", "AURA Investigation"),
        )

        self._center_text(
            draw,
            scene.get(
                "purpose",
                "AI-powered fraud investigation",
            ),
            self.width // 2,
            self.height // 2,
            self.font_large,
            self.BLACK,
        )

    # ------------------------------------------------------------------
    # UI HELPERS
    # ------------------------------------------------------------------

    def _draw_title(
        self,
        draw: ImageDraw.ImageDraw,
        title: str,
    ) -> None:

        draw.text(
            (120, 100),
            "AURA",
            font=self.font_medium,
            fill=self.PINK,
        )

        draw.text(
            (120, 170),
            self._clean_text(title),
            font=self.font_large,
            fill=self.BLACK,
        )

    def _draw_card(
        self,
        draw: ImageDraw.ImageDraw,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> None:

        draw.rounded_rectangle(
            (x1, y1, x2, y2),
            radius=30,
            fill=self.WHITE,
            outline=self.LIGHT_GREY,
            width=2,
        )

    def _draw_branding(
        self,
        image: Image.Image,
    ) -> None:

        draw = ImageDraw.Draw(image)

        draw.text(
            (80, self.height - 85),
            "AURA • AI Fraud Intelligence",
            font=self.font_small,
            fill=self.GREY,
        )

        draw.text(
            (
                self.width - 420,
                self.height - 85,
            ),
            "CONFIDENTIAL",
            font=self.font_small,
            fill=self.GREY,
        )

    def _center_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        font: ImageFont.FreeTypeFont,
        fill: tuple,
    ) -> None:

        bbox = draw.textbbox(
            (0, 0),
            str(text),
            font=font,
        )

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        draw.text(
            (
                x - text_width / 2,
                y - text_height / 2,
            ),
            str(text),
            font=font,
            fill=fill,
        )

    # ------------------------------------------------------------------
    # UTILITIES
    # ------------------------------------------------------------------

    def _format_amount(self, amount: Any) -> str:

        try:
            return f"${float(amount):,.2f}"
        except (TypeError, ValueError):
            return str(amount)

    def _clean_text(self, value: Any) -> str:

        text = str(value).strip()

        if text:
            return text[0].upper() + text[1:]

        return text

    def compile_mp4(
        self,
        render_result: Dict[str, Any],
        output_name: str = "aura_investigation",
    ) -> Optional[str]:
        """
        Assemble all rendered scene frames into an MP4 file using FFmpeg.
        Returns the path to the MP4 file if successful, or None.
        """
        scenes = render_result.get("scenes", [])
        if not scenes:
            return None

        output_dir = Path(render_result.get("output_directory", self.output_dir / output_name))
        final_mp4 = output_dir / f"{output_name}.mp4"

        try:
            test_run = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if test_run.returncode != 0:
                return None

            concat_list = output_dir / "concat_scenes.txt"
            scene_mp4s = []

            for scene_info in scenes:
                scene_num = scene_info.get("scene_number", 1)
                scene_dir = Path(scene_info.get("frame_directory"))
                scene_mp4 = scene_dir / f"scene_{scene_num:02d}.mp4"

                cmd = [
                    "ffmpeg", "-y",
                    "-framerate", str(self.fps),
                    "-i", str(scene_dir / "frame_%05d.png"),
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-preset", "fast",
                    str(scene_mp4),
                ]
                subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                scene_mp4s.append(scene_mp4)

            with open(concat_list, "w", encoding="utf-8") as f:
                for smp4 in scene_mp4s:
                    resolved = smp4.resolve()
                    escaped = str(resolved).replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

            concat_cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(final_mp4),
            ]
            subprocess.run(
                concat_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

            if final_mp4.exists():
                return str(final_mp4)
        except Exception:
            return None

        return None


def render_video_scenes(
    video_data: Dict[str, Any],
    output_name: str = "aura_investigation",
    assemble_mp4: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function for rendering SceneGenerator output.
    """

    renderer = VideoRenderer()

    result = renderer.render(
        video_data,
        output_name=output_name,
    )

    if assemble_mp4:
        mp4_path = renderer.compile_mp4(result, output_name=output_name)
        result["mp4_path"] = mp4_path

    return result