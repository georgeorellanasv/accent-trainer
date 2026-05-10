import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from services.azure_tts import get_tts_audio
from database import get_connection

router = APIRouter(prefix="/api/tts", tags=["tts"])

def _get_db_path():
    return os.environ.get("TEST_DB_PATH") or None

@router.get("/phrase/{phrase_id}")
def get_phrase_audio(
    phrase_id: int,
    user_id: str = Query(..., description="User ID to get voice preference")
):
    """
    Get TTS audio for a phrase using user's voice preference.
    Returns WAV audio.
    """
    # Get user's voice preference
    with get_connection(_get_db_path()) as conn:
        user_row = conn.execute(
            "SELECT voice_preference FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    if not user_row:
        raise HTTPException(404, "User not found")

    voice = user_row["voice_preference"]

    # Get phrase text - we need to load from phrases files
    phrase_text = _get_phrase_text(phrase_id)
    if not phrase_text:
        raise HTTPException(404, "Phrase not found")

    audio_bytes = get_tts_audio(phrase_text, voice)

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": f"inline; filename=phrase_{phrase_id}.wav"}
    )

@router.get("/text")
def get_text_audio(
    text: str = Query(..., description="Text to synthesize"),
    voice: str = Query("female", description="Voice: male or female")
):
    """
    Get TTS audio for arbitrary text.
    Returns WAV audio.
    """
    if len(text) > 500:
        raise HTTPException(400, "Text too long (max 500 characters)")

    audio_bytes = get_tts_audio(text, voice)

    return Response(
        content=audio_bytes,
        media_type="audio/wav"
    )

def _get_phrase_text(phrase_id: int) -> Optional[str]:
    """Load phrase text from JSON files."""
    import json
    from pathlib import Path

    data_dir = Path(__file__).parent.parent / "data"

    # Check all level files
    for level in range(1, 7):
        level_file = data_dir / f"phrases_level_{level}.json"
        if level_file.exists():
            phrases = json.loads(level_file.read_text())
            for p in phrases:
                if p["id"] == phrase_id:
                    return p["en"]

    # Check legacy phrases.json
    legacy_file = data_dir.parent / "phrases.json"
    if legacy_file.exists():
        phrases = json.loads(legacy_file.read_text())
        for p in phrases:
            if p["id"] == phrase_id:
                return p["en"]

    return None
