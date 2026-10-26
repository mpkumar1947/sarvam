import base64
import json
import os
import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sarvamai import SarvamAI

ROOT = Path(__file__).parent
env = ROOT / ".env"
if env.exists():
    for line in env.read_text().splitlines():
        k, _, v = line.partition("=")
        if k.strip() and not k.lstrip().startswith("#"):
            os.environ.setdefault(k.strip(), v.strip())

KEY = os.environ.get("SARVAM_API_KEY")
if not KEY:
    raise SystemExit("SARVAM_API_KEY is empty, paste it into .env")
client = SarvamAI(api_subscription_key=KEY)

TTS_LANGS = {"bn-IN", "en-IN", "gu-IN", "hi-IN", "kn-IN", "ml-IN", "mr-IN", "od-IN", "pa-IN", "ta-IN", "te-IN"}
CATEGORIES = [
    "Railways", "Pension", "Banking & Finance", "Telecom & Post", "Income Tax & GST",
    "Passport & Visa", "Health", "Education", "Water Supply", "Electricity",
    "Roads & Transport", "Municipal & Sanitation", "Police & Law", "Ration & Food Supply",
    "LPG & Petroleum", "Land & Revenue", "Labour & Employment", "Other",
]

SYSTEM = f"""You turn a citizen's spoken complaint into a grievance for CPGRAMS (pgportal.gov.in), India's central public grievance portal.
The complaint may be in any Indian language, romanized or code-mixed, and may ramble. Work only from what the citizen said.

Return ONLY a JSON object with these keys:
"subject": one line, at most 15 words, English
"category": exactly one of {json.dumps(CATEGORIES)}. Pension problems are always "Pension", even if the bank is involved.
"department": the body that should handle it, e.g. "Ministry of Railways", "Department of Pension & Pensioners' Welfare", "Department of Financial Services (Banking Division)". Water, electricity, municipal, police, land and ration-shop issues are usually State subjects: write "Government of <State> - <Department>" if the state is known, else "State Government - <Department>". Pension routing: railway pensioners -> "Ministry of Railways"; defence pensioners -> "Department of Ex-Servicemen Welfare"; other central civil pensioners -> "Department of Pension & Pensioners' Welfare"; pension stuck at the bank -> "Department of Financial Services (Banking Division)".
"location": city, town or area name only (not an office), else ""
"incident_date": date or duration mentioned (e.g. "for the last 3 weeks"), else ""
"grievance_text": formal English, first person, 100 to 180 words. State the facts, what was already tried, and the impact. Never invent names, numbers, dates, IDs or places. If something important is missing, use a bracketed placeholder like [PPO number].
"relief_sought": one sentence, English
"urgency": "low", "medium" or "high" (high only for health, safety, or loss of basic services or income)
"missing_info": up to 3 short questions asking for details that would strengthen the grievance (IDs, dates, office names), in the citizen's language. No brackets or placeholders here, say the detail in plain words.
"readback": 2 to 3 short sentences in the citizen's language and script telling them what will be filed and to which department, so they can confirm by listening. No brackets or placeholders here, say the detail in plain words."""


def transcribe(data, name="audio.wav", mime="audio/wav"):
    r = client.speech_to_text.transcribe(
        file=(name, data, mime), model="saaras:v4", mode="transcribe", language_code="unknown"
    )
    return r.transcript, r.language_code


def draft(text, lang=None):
    r = client.chat.completions(
        model="sarvam-105b",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Citizen's language: {lang or 'same as the complaint'}\n\nComplaint:\n{text}"},
        ],
        temperature=0.2,
        max_tokens=4096,
        reasoning_effort=None,
        response_format={"type": "json_object"},
    )
    raw = r.choices[0].message.content or ""
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError(f"model did not return JSON: {raw[:200]}")
    g = json.loads(m.group(0))
    if g.get("category") not in CATEGORIES:
        g["category"] = "Other"
    mi = g.get("missing_info") or []
    if isinstance(mi, str):
        mi = re.split(r"\s*\d+[.)]\s+|\n+", mi)
    g["missing_info"] = [re.sub(r"^\d+[.)]\s*", "", str(x)).strip() for x in mi if str(x).strip()][:3]
    if g.get("urgency") not in ("low", "medium", "high"):
        g["urgency"] = "medium"
    for k in ("subject", "department", "location", "incident_date", "grievance_text", "relief_sought", "readback"):
        g[k] = str(g.get(k) or "")
    return g


def speak(text, lang):
    lang = lang if lang in TTS_LANGS else "hi-IN"
    try:
        r = client.text_to_speech.convert(
            text=text[:1500], language_code=lang, model="bulbul:v3", speaker="shubh", output_audio_codec="mp3"
        )
    except Exception:
        r = client.text_to_speech.convert(
            text=text[:1500], language_code=lang, model="bulbul:v4-flash", output_audio_codec="mp3"
        )
    return base64.b64encode(b"".join(base64.b64decode(a) for a in r.audios)).decode()


app = FastAPI(title="Shikayat Saathi")


class DraftIn(BaseModel):
    text: str
    language_code: str | None = None


class SpeakIn(BaseModel):
    text: str
    language_code: str | None = None


def fail(e):
    raise HTTPException(502, f"{type(e).__name__}: {str(e)[:300]}")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/transcribe")
def api_transcribe(file: UploadFile = File(...)):
    data = file.file.read()
    if len(data) > 5_000_000:
        raise HTTPException(413, "audio too large")
    try:
        t, lang = transcribe(data, file.filename or "audio.wav", file.content_type or "audio/wav")
    except Exception as e:
        fail(e)
    return {"transcript": t, "language_code": lang}


@app.post("/api/draft")
def api_draft(body: DraftIn):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "empty complaint")
    try:
        return draft(text[:4000], body.language_code)
    except Exception as e:
        fail(e)


@app.post("/api/speak")
def api_speak(body: SpeakIn):
    if not body.text.strip():
        raise HTTPException(400, "empty text")
    try:
        return {"audio": speak(body.text, body.language_code)}
    except Exception as e:
        fail(e)


app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="static")
