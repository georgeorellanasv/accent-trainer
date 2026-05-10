import os
import azure.cognitiveservices.speech as speechsdk
from fastapi import HTTPException

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
    phoneme_details = []

    for w in pa.words:
        phonemes = [
            {"phoneme": p.phoneme, "accuracy": round(p.accuracy_score, 1)}
            for p in (w.phonemes or [])
        ]
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
