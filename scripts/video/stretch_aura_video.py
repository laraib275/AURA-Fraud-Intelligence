import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
VIDEO_DIR = PROJECT / "data" / "video"
INPUT = VIDEO_DIR / "aura_story_raw.mp4"
OUTPUT = VIDEO_DIR / "aura_story_32s.mp4"

TARGET = 32.412834

probe = subprocess.run(
    [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(INPUT),
    ],
    capture_output=True,
    text=True,
    check=True,
)

source_duration = float(probe.stdout.strip())
speed = source_duration / TARGET

print(f"Source duration : {source_duration:.3f} sec")
print(f"Target duration : {TARGET:.3f} sec")
print(f"Video speed     : {speed:.4f}x")

subprocess.run(
    [
        "ffmpeg", "-y",
        "-i", str(INPUT),
        "-filter_complex",
        f"[0:v]setpts={1/speed:.6f}*PTS,fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p[v]",
        "-map", "[v]",
        "-an",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-movflags", "+faststart",
        str(OUTPUT),
    ],
    check=True,
)

print()
print("SUCCESS")
print(f"Created: {OUTPUT}")
