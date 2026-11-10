import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIDEO_DIR = ROOT / "data" / "video"
VIDEO = VIDEO_DIR / "aura_story_narrated.mp4"
ASS = VIDEO_DIR / "aura_story_captions.ass"
OUTPUT = VIDEO_DIR / "aura_story_final.mp4"

if not VIDEO.exists():
    raise FileNotFoundError(f"Video not found: {VIDEO}")
if not ASS.exists():
    raise FileNotFoundError(f"Caption file not found: {ASS}")

# Use a project-relative subtitle path so FFmpeg does not interpret
# the Windows C: drive colon as an ASS-filter option separator.
ass_relative = ASS.relative_to(ROOT).as_posix()

print("Burning synchronized AURA captions into the narrated video...")
print(f"Video   : {VIDEO}")
print(f"Captions: {ASS}")

subprocess.run(
    [
        "ffmpeg", "-y",
        "-i", str(VIDEO),
        "-vf", f"ass={ass_relative}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(OUTPUT),
    ],
    cwd=str(ROOT),
    check=True,
)

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

print()
print("SUCCESS")
print(f"Final video: {OUTPUT}")
print(f"Duration: {float(probe.stdout.strip()):.3f} seconds")
