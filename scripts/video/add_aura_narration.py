import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
VIDEO_DIR = PROJECT / "data" / "video"

VIDEO = VIDEO_DIR / "aura_story_32s.mp4"
AUDIO = VIDEO_DIR / "aura_narration.wav"
OUTPUT = VIDEO_DIR / "aura_story_narrated.mp4"

if not VIDEO.exists():
    raise FileNotFoundError(f"Video not found: {VIDEO}")

if not AUDIO.exists():
    raise FileNotFoundError(f"Narration not found: {AUDIO}")

print("Combining AURA video and narration...")

subprocess.run(
    [
        "ffmpeg", "-y",
        "-i", str(VIDEO),
        "-i", str(AUDIO),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(OUTPUT),
    ],
    check=True,
)

print()
print("SUCCESS")
print(f"Created: {OUTPUT}")

# Verify final duration
probe = subprocess.run(
    [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(OUTPUT),
    ],
    capture_output=True,
    text=True,
    check=True,
)

print(f"Final duration: {float(probe.stdout.strip()):.3f} seconds")
