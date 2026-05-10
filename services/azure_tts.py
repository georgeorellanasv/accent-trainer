import os
import azure.cognitiveservices.speech as speechsdk
from fastapi import HTTPException
from pathlib import Path
import hashlib

CACHE_DIR = Path(__file__).parent.parent / "data" / "tts_cache"

def get_tts_audio(text: str, voice: str = "female") -> bytes:
    """
    Generate TTS audio using Azure Neural voices.
    voice: "male" -> en-GB-RyanNeural, "female" -> en-GB-SoniaNeural
    Returns: WAV audio bytes
    """
    key = os.environ.get("AZURE_SPEECH_KEY", "")
    region = os.environ.get("AZURE_SPEECH_REGION", "eastus")
    if not key:
        raise HTTPException(503, "AZURE_SPEECH_KEY not configured")

    voice_name = "en-GB-RyanNeural" if voice == "male" else "en-GB-SoniaNeural"

    # Check cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.md5(f"{text}:{voice_name}".encode()).hexdigest()
    cache_path = CACHE_DIR / f"{cache_key}.wav"

    if cache_path.exists():
        return cache_path.read_bytes()

    # Generate TTS
    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_synthesis_voice_name = voice_name
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    )

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None  # Return audio data directly
    )

    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        audio_data = result.audio_data
        # Cache for future use
        cache_path.write_bytes(audio_data)
        return audio_data
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        raise HTTPException(502, f"TTS failed: {cancellation.reason} - {cancellation.error_details}")
    else:
        raise HTTPException(502, f"TTS failed: {result.reason}")


def clear_cache() -> int:
    """Clear TTS cache. Returns number of files deleted."""
    if not CACHE_DIR.exists():
        return 0
    count = 0
    for f in CACHE_DIR.glob("*.wav"):
        f.unlink()
        count += 1
    return count
