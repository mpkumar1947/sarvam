import base64
import json
from pathlib import Path

from app import draft, speak, transcribe

SAMPLE = "मेरे पिताजी रेलवे से रिटायर हुए हैं। पिछले चार महीने से उनकी पेंशन बैंक खाते में नहीं आई है। दो बार ऑफिस जा चुके हैं, कोई सुनवाई नहीं हुई। कृपया जल्दी पेंशन चालू करवाइए।"

print("1/4 chat (sarvam-105b) ...")
g = draft(SAMPLE, "hi-IN")
print(json.dumps(g, ensure_ascii=False, indent=2))

print("\n2/4 tts hi-IN (bulbul) ...")
mp3 = base64.b64decode(speak(g["readback"], "hi-IN"))
Path("check_hi.mp3").write_bytes(mp3)
print(f"ok, {len(mp3)} bytes -> check_hi.mp3")

print("\n3/4 stt round trip (saaras:v4) ...")
t, lang = transcribe(mp3, "check_hi.mp3", "audio/mpeg")
print(f"lang={lang}\n{t}")

print("\n4/4 tts ta-IN ...")
ta = base64.b64decode(speak("உங்கள் புகார் பதிவு செய்யப்பட்டது.", "ta-IN"))
Path("check_ta.mp3").write_bytes(ta)
print(f"ok, {len(ta)} bytes -> check_ta.mp3")

print("\nALL CHECKS PASSED")
