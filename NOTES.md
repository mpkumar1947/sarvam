# Verified API facts (checked against docs.sarvam.ai + sarvamai 0.1.39 on 2026-10-26)

Use these instead of guessing. Docs for agents: https://docs.sarvam.ai/llms.txt (append .md to any docs page).

## Chat: `client.chat.completions(...)`
- Models: `sarvam-105b` (128K ctx, reasoning) and `sarvam-105b-conversations` (32K, dialogue).
- Reasoning is ON by default (`reasoning_effort` low/high/max, or None to disable). Reasoning tokens count against `max_tokens`, so a small max_tokens can return an empty answer. Starter plan cap: 4096.
- `response_format={"type": "json_object"}` is supported. `app.py` still regex-extracts the `{...}` block to be safe.
- Reply: `r.choices[0].message.content`

## Speech to Text: `client.speech_to_text.transcribe(...)`
- Models: `saaras:v4` (default, recommended), `saaras:v3`.
- `language_code="unknown"` = auto-detect. The response has `transcript`, `language_code`, `language_probability`.
- REST limit: **30 s per request**. Recommended input is 16 kHz mono WAV (that's what the frontend sends).
- Documented formats: WAV, MP3, AAC, FLAC, OGG.

## Text to Speech: `client.text_to_speech.convert(...)`
- Models: `bulbul:v3` (11 langs: bn, en, gu, hi, kn, ml, mr, od, pa, ta, te, all `-IN`), `bulbul:v4-flash` (fewer langs, speaker ids like `ritu_hi_customer`).
- `bulbul:v3` speaker used: `shubh` (male, confirmed in docs). If it errors, `app.py` falls back to v4-flash with its default voice.
- Response: `r.audios` = list of base64 chunks. Decode each and concat the bytes. Don't concat the base64 strings.

## Errors
- 403 = bad or revoked key. 429 = rate limit or credits. 400 with "speaker" = speaker not valid for that model/language.
