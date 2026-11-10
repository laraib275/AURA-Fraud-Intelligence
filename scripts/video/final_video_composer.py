import subprocess
import sys
from pathlib import Path

PROJECT = Path(r"C:\Users\HP\Desktop\AURA-Fraud-Intelligence")
INPUT = PROJECT / "data" / "video" / "aura_story_raw.mp4"
OUTPUT = PROJECT / "data" / "video" / "aura_story_branded.mp4"
ASS = PROJECT / "data" / "video" / "aura_story_captions.ass"

def run(cmd):
    print(">", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)

def ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    whole = int(s)
    centi = int(round((s - whole) * 100))
    if centi == 100:
        whole += 1
        centi = 0
    return f"{h}:{m:02d}:{whole:02d}.{centi:02d}"

def make_ass():
    # Timings are based on the six ~3.56s Wan clips currently assembled.
    events = [
        (0.00, 3.45, "AURA — THE STORY BEHIND A SUSPICIOUS TRANSACTION", "title"),
        (0.45, 3.35, "A digital payment appears normal.", "caption"),
        (3.56, 7.05, "But AURA detects unusual activity.", "caption"),
        (7.12, 10.58, "Multiple signals raise the risk.", "caption"),
        (7.55, 10.55, "AURA RISK SCORE   81.28   •   CRITICAL", "risk"),
        (10.69, 14.15, "AURA traces connected financial activity.", "caption"),
        (11.10, 13.90, "GRAPH RISK   17.33   •   LOW", "graph"),
        (14.25, 17.70, "AI Investigator connects the evidence.", "caption"),
        (17.82, 21.05, "IMMEDIATE INVESTIGATION", "decision"),
        (18.35, 21.05, "Human review required.", "caption"),
        (20.45, 21.28, "AURA  |  AI FRAUD INTELLIGENCE", "brand"),
    ]

    ass_text = r"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: title,Arial,42,&H00FFFFFF,&H00FFFFFF,&H001A1020,&H99000000,-1,0,0,0,100,100,1,0,1,2,1,8,90,90,55,1
Style: caption,Arial,34,&H00FFFFFF,&H00FFFFFF,&H001A1020,&H99000000,0,0,0,0,100,100,0,0,1,2,1,2,120,120,75,1
Style: risk,Arial,44,&H00FFFFFF,&H00FFFFFF,&H001A1020,&HCCB00055,-1,0,0,0,100,100,0,0,1,2,1,7,90,90,75,1
Style: graph,Arial,38,&H00FFFFFF,&H00FFFFFF,&H001A1020,&HCC332244,-1,0,0,0,100,100,0,0,1,2,1,7,90,90,130,1
Style: decision,Arial,52,&H00FFFFFF,&H00FFFFFF,&H001A1020,&HCCB00055,-1,0,0,0,100,100,1,0,1,2,1,8,90,90,65,1
Style: brand,Arial,26,&H00FFFFFF,&H00FFFFFF,&H001A1020,&H99000000,-1,0,0,0,100,100,2,0,1,1,1,2,80,80,35,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [ass_text]
    for start, end, text, style in events:
        safe = text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")
        lines.append(
            f"Dialogue: 0,{ass_time(start)},{ass_time(end)},{style},,0,0,0,,{safe}\n"
        )
    ASS.parent.mkdir(parents=True, exist_ok=True)
    ASS.write_text("".join(lines), encoding="utf-8")

def main():
    if not INPUT.exists():
        print("ERROR: Raw video not found:")
        print(INPUT)
        sys.exit(1)

    make_ass()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Burn the controlled AURA story captions into the AI-generated video.
    run([
        "ffmpeg", "-y",
        "-i", str(INPUT),
        "-vf", f"subtitles={ASS.as_posix().replace(':', r'\\:')}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-an",
        "-movflags", "+faststart",
        str(OUTPUT),
    ])

    print("\nSUCCESS")
    print("Branded video:", OUTPUT)
    print("Caption file:", ASS)

if __name__ == "__main__":
    main()
