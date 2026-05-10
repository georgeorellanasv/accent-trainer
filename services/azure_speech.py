import os
import json
import azure.cognitiveservices.speech as speechsdk
from fastapi import HTTPException

def log_debug(msg):
    with open("/tmp/azure_debug.log", "a") as f:
        f.write(msg + "\n")

def run_assessment(wav_path: str, reference_text: str) -> dict:
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
    pronunciation_config.phoneme_alphabet = "IPA"  # Request IPA phoneme symbols

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

    # Debug: log raw JSON from Azure to file
    try:
        raw_json = json.loads(result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult, "{}"))
        log_debug(f"[RAW JSON]: {json.dumps(raw_json, indent=2)}")
    except Exception as e:
        log_debug(f"[ERROR] Could not parse raw JSON: {e}")

    word_scores = []
    phoneme_details = []

    for w in pa.words:
        phonemes = []
        for p in (w.phonemes or []):
            # Get phoneme text
            phoneme_str = p.phoneme
            log_debug(f"[PHONEME] word={w.word}, phoneme={phoneme_str}, accuracy={p.accuracy_score}")
            phonemes.append({
                "phoneme": phoneme_str,
                "accuracy": round(p.accuracy_score, 1)
            })
        phoneme_details.extend(phonemes)

        worst = min(phonemes, key=lambda x: x["accuracy"]) if phonemes else None
        word_scores.append({
            "word": w.word,
            "accuracy": round(w.accuracy_score, 1),
            "error_type": str(w.error_type) if w.error_type else "None",
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
        "phoneme_details": phoneme_details,
    }
