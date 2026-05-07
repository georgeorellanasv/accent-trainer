import os
import ssl
import json
import tempfile
from pathlib import Path

# Corporate SSL bypass
ssl._create_default_https_context = ssl._create_unverified_context
os.environ.setdefault("CURL_CA_BUNDLE", "")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "")

import azure.cognitiveservices.speech as speechsdk
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

load_dotenv()

app = FastAPI(title="Posh English Trainer API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

PHRASES_PATH = Path(__file__).parent / "phrases.json"
phrases: dict[int, dict] = {}

@app.on_event("startup")
def load_phrases():
    global phrases
    data = json.loads(PHRASES_PATH.read_text(encoding="utf-8"))
    phrases = {p["id"]: p for p in data}


# ── Cerebras client ───────────────────────────────────────────────────────────

def get_cerebras() -> OpenAI:
    key = os.environ.get("CEREBRAS_API_KEY", "")
    if not key:
        raise HTTPException(503, "CEREBRAS_API_KEY not configured")
    return OpenAI(base_url="https://api.cerebras.ai/v1", api_key=key)


COACHING_SYSTEM = """You are a concise RP (Received Pronunciation) accent coach for Latin American Spanish speakers.
You receive Azure Pronunciation Assessment data with exact scores per word and phoneme.
Give specific, actionable tips for words that scored below 80.

Common Spanish→RP errors to reference:
- /θ/ (thin) → said as /s/ or /t/
- /ð/ (the, this) → said as /d/
- Non-rhotic R: RP drops R after vowels (water=/ˈwɔːtə/) — Spanish speakers keep it
- /ɪ/ vs /iː/ — Spanish only has one /i/
- /ɑː/ bath broadening (bath, dance, can't) — Spanish speakers use /a/
- /ʌ/ (cup, but) → said as /a/
- RP diphthongs: /əʊ/ not /oʊ/, /eɪ/ in day

Return ONLY valid JSON:
{
  "tips": [{"word": str, "tip": str, "phoneme_focus": str}],
  "focus": str,
  "encouragement": str
}
Keep tips under 25 words each. Be warm but precise."""


def get_coaching(phrase: dict, word_scores: list, attempt: int) -> dict:
    try:
        cerebras = get_cerebras()
        problem_words = [w for w in word_scores if w["accuracy"] < 80]
        user_msg = (
            f'Phrase: "{phrase["en"]}"\n'
            f'IPA RP: {phrase["ipa_rp"]}\n'
            f'Target phonemes: {", ".join(phrase["target_phonemes"])}\n'
            f'Attempt #{attempt}\n\n'
            f'Word scores (Azure):\n' +
            "\n".join(
                f'  {w["word"]}: {w["accuracy"]:.0f}/100'
                + (f' — worst phoneme: /{w["worst_phoneme"]}/ ({w["worst_phoneme_score"]:.0f}/100)' if w.get("worst_phoneme") else "")
                for w in word_scores
            ) +
            f'\n\nProblem words: {[w["word"] for w in problem_words]}'
        )
        resp = cerebras.chat.completions.create(
            model="llama-3.3-70b",
            max_tokens=512,
            messages=[
                {"role": "system", "content": COACHING_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        # Fallback: return phrase notes as focus
        return {
            "tips": [],
            "focus": phrase["notes"],
            "encouragement": "Keep practising — every attempt counts!",
        }


# ── Azure Pronunciation Assessment ───────────────────────────────────────────

def run_azure_assessment(wav_path: str, reference_text: str) -> dict:
    key = os.environ.get("AZURE_SPEECH_KEY", "")
    region = os.environ.get("AZURE_SPEECH_REGION", "eastus")
    if not key:
        raise HTTPException(503, "AZURE_SPEECH_KEY not configured")

    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_recognition_language = "en-GB"

    pronunciation_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=reference_text,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
        enable_miscue=True,
    )

    audio_config = speechsdk.audio.AudioConfig(filename=wav_path)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config
    )
    pronunciation_config.apply_to(recognizer)

    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.NoMatch:
        raise HTTPException(422, "Azure could not recognize speech — speak closer to the mic")
    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        raise HTTPException(502, f"Azure recognition failed: {result.reason}")

    pa = speechsdk.PronunciationAssessmentResult(result)

    word_scores = []
    for w in pa.words:
        phonemes = [
            {"phoneme": p.phoneme, "accuracy": round(p.accuracy_score, 1)}
            for p in (w.phonemes or [])
        ]
        worst = min(phonemes, key=lambda x: x["accuracy"]) if phonemes else None
        word_scores.append({
            "word": w.word,
            "accuracy": round(w.accuracy_score, 1),
            "error_type": w.error_type.name if w.error_type else "None",
            "status": "ok" if w.accuracy_score >= 80 else ("warn" if w.accuracy_score >= 55 else "error"),
            "phonemes": phonemes,
            "worst_phoneme": worst["phoneme"] if worst else None,
            "worst_phoneme_score": worst["accuracy"] if worst else None,
        })

    return {
        "pron_score": round(pa.pronunciation_score, 1),
        "accuracy": round(pa.accuracy_score, 1),
        "fluency": round(pa.fluency_score, 1),
        "completeness": round(pa.completeness_score, 1),
        "transcription": result.text,
        "words": word_scores,
    }


# ── /assess endpoint ──────────────────────────────────────────────────────────

@app.post("/assess")
async def assess(
    audio: UploadFile = File(...),
    phrase_id: int = Form(...),
    attempt: int = Form(1),
):
    if phrase_id not in phrases:
        raise HTTPException(404, "Phrase not found")
    phrase = phrases[phrase_id]

    content = await audio.read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(content)
        wav_path = tmp.name

    try:
        azure_result = run_azure_assessment(wav_path, phrase["en"])
    finally:
        os.unlink(wav_path)

    coaching = get_coaching(phrase, azure_result["words"], attempt)

    return JSONResponse({
        "score": round(azure_result["pron_score"] / 10, 1),
        "accuracy": azure_result["accuracy"],
        "fluency": azure_result["fluency"],
        "completeness": azure_result["completeness"],
        "transcription": azure_result["transcription"],
        "words": azure_result["words"],
        "tips": coaching.get("tips", []),
        "focus": coaching.get("focus", phrase["notes"]),
        "encouragement": coaching.get("encouragement", ""),
    })


# ── Phrases + serve app ───────────────────────────────────────────────────────

@app.get("/phrases")
def list_phrases():
    return list(phrases.values())


@app.get("/")
def serve_app():
    return FileResponse(Path(__file__).parent / "app.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8001, reload=False)
