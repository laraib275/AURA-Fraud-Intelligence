from pathlib import Path

import pyttsx3

OUTPUT = Path("data/video/aura_narration.wav")

text = """
A digital payment appears normal.

But AURA detects signals that demand attention.

Behavioural and anomaly analysis raise the transaction risk to eighty-one point two-eight — critical.

AURA then looks beyond the transaction, uncovering connected activity across the network.

Its AI Investigator brings the evidence together and explains what matters.

The result is clear: immediate investigation and human review are required.

AURA — turning suspicious activity into actionable intelligence.
"""

engine = pyttsx3.init()

# Try to select a female English voice if one is available.
voices = engine.getProperty("voices")
for voice in voices:
    name = voice.name.lower()
    if "female" in name or "zira" in name or "susan" in name:
        engine.setProperty("voice", voice.id)
        break

engine.setProperty("rate", 155)
engine.setProperty("volume", 1.0)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

engine.save_to_file(text, str(OUTPUT))
engine.runAndWait()

print("SUCCESS")
print(f"Narration saved to: {OUTPUT.resolve()}")