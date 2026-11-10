import subprocess
import sys
from pathlib import Path

PROJECT = Path(r"C:\Users\HP\Desktop\AURA-Fraud-Intelligence")
CLIPS = PROJECT / "data" / "video" / "final_clips"
WORK = PROJECT / "data" / "video" / "assembly"
NORMALIZED = WORK / "normalized"
OUTPUT = PROJECT / "data" / "video" / "aura_story_raw.mp4"

EXPECTED = [CLIPS / f"scene_{i}.mp4" for i in range(1, 7)]

def run(cmd):
    print(">", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)

def main():
    missing = [p for p in EXPECTED if not p.exists()]
    if missing:
        print("ERROR: Missing clip(s):")
        for p in missing:
            print(" -", p)
        sys.exit(1)

    WORK.mkdir(parents=True, exist_ok=True)
    NORMALIZED.mkdir(parents=True, exist_ok=True)

    # Normalize all six clips to the same format before concatenation.
    for i, src in enumerate(EXPECTED, 1):
        dst = NORMALIZED / f"scene_{i:02d}.mp4"
        print(f"\nNormalizing Scene {i}...")
        run([
            "ffmpeg", "-y",
            "-i", str(src),
            "-vf",
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "-r", "30",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-an",
            str(dst),
        ])

    concat_file = WORK / "concat.txt"
    with concat_file.open("w", encoding="utf-8") as f:
        for i in range(1, 7):
            # ffmpeg concat demuxer requires escaped single quotes in paths.
            path = (NORMALIZED / f"scene_{i:02d}.mp4").resolve()
            f.write(f"file '{str(path).replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")

    print("\nCombining all six scenes...")
    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        "-movflags", "+faststart",
        str(OUTPUT),
    ])

    print("\nSUCCESS")
    print("Output:", OUTPUT)

if __name__ == "__main__":
    main()
