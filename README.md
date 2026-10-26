# Shikayat Saathi

Speak a complaint in any Indian language, get a ready-to-file grievance for CPGRAMS (pgportal.gov.in).

Most citizens who need the grievance portal can't write a formal English complaint, can't tell which ministry handles their issue, and give up. Shikayat Saathi lets them just talk.

## Flow

1. **Bolo (speak):** record up to 29 s in the browser, or upload a voice note. Record again to add details.
2. **Jaancho (check):** Sarvam-105B turns the transcript into a structured grievance (subject, category, department, location, date, formal English text, relief sought, urgency) and lists what's missing. Bulbul reads a confirmation back in the citizen's own language.
3. **Bhejo (file):** copy or download the grievance and paste it into pgportal.gov.in.

## Sarvam APIs used

| Step | API | Model |
|---|---|---|
| Voice to text, language auto-detect | Speech to Text | `saaras:v4` |
| Drafting + department routing | Chat Completions (JSON mode) | `sarvam-105b` |
| Spoken read-back | Text to Speech | `bulbul:v3` (fallback `bulbul:v4-flash`) |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then paste your key into .env with an editor
python check.py         # one call to each API
uvicorn app:app --port 8000
```

Open http://localhost:8000. The API key stays on the server and is never sent to the browser.

## Notes

- Browser audio is converted to 16 kHz mono WAV client-side, so any format the browser can record or decode works.
- Sarvam's REST speech-to-text takes up to 30 s per request, so recordings are capped at 29 s. Record multiple times for longer complaints.
- The model is told never to invent IDs, names or dates. It uses `[placeholders]` and asks for missing details instead.
- Always review a draft before filing.
