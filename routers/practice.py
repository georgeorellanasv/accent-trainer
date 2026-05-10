import os
import json
import tempfile
from typing import Dict
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from database import get_connection
from services.azure_speech import run_assessment
from services.cerebras import get_coaching
from services.scoring import calculate_strict_score, get_phoneme_scores

router = APIRouter(prefix="/api", tags=["practice"])

def _get_db_path():
    return os.environ.get("TEST_DB_PATH") or None

# Cache for phrases
_phrases_cache: Dict[int, dict] = {}

def _load_phrases():
    global _phrases_cache
    if _phrases_cache:
        return _phrases_cache

    data_dir = Path(__file__).parent.parent / "data"

    # Load from level files
    for level in range(1, 7):
        level_file = data_dir / f"phrases_level_{level}.json"
        if level_file.exists():
            phrases = json.loads(level_file.read_text())
            for p in phrases:
                p["level"] = level
                _phrases_cache[p["id"]] = p

    # Load legacy phrases if no level files exist
    if not _phrases_cache:
        legacy_file = data_dir.parent / "phrases.json"
        if legacy_file.exists():
            phrases = json.loads(legacy_file.read_text())
            for p in phrases:
                p["level"] = 1  # Default to level 1
                _phrases_cache[p["id"]] = p

    return _phrases_cache

@router.get("/phrases")
def list_phrases():
    """Get all phrases."""
    phrases = _load_phrases()
    return list(phrases.values())

@router.get("/levels")
def get_levels(user_id: str):
    """Get journey map with level progress for a user."""
    with get_connection(_get_db_path()) as conn:
        rows = conn.execute(
            """SELECT level, completed, avg_score, phrases_practiced
               FROM level_progress WHERE user_id = ?""",
            (user_id,)
        ).fetchall()

    progress = {row["level"]: dict(row) for row in rows}

    levels = [
        {
            "level": 1,
            "name": "Sonidos que no existen",
            "phonemes": ["/θ/", "/ð/"],
            "completed": progress.get(1, {}).get("completed", False),
            "avg_score": progress.get(1, {}).get("avg_score", 0),
            "phrases_practiced": progress.get(1, {}).get("phrases_practiced", 0),
        },
        {
            "level": 2,
            "name": "Vocales confusas",
            "phonemes": ["/ɪ/", "/iː/", "/æ/", "/ʌ/"],
            "completed": progress.get(2, {}).get("completed", False),
            "avg_score": progress.get(2, {}).get("avg_score", 0),
            "phrases_practiced": progress.get(2, {}).get("phrases_practiced", 0),
        },
        {
            "level": 3,
            "name": "La R británica",
            "phonemes": ["non-rhotic", "linking R"],
            "completed": progress.get(3, {}).get("completed", False),
            "avg_score": progress.get(3, {}).get("avg_score", 0),
            "phrases_practiced": progress.get(3, {}).get("phrases_practiced", 0),
        },
        {
            "level": 4,
            "name": "Ritmo y reducción",
            "phonemes": ["/ə/", "weak forms"],
            "completed": progress.get(4, {}).get("completed", False),
            "avg_score": progress.get(4, {}).get("avg_score", 0),
            "phrases_practiced": progress.get(4, {}).get("phrases_practiced", 0),
        },
        {
            "level": 5,
            "name": "Diptongos RP",
            "phonemes": ["/əʊ/", "/eɪ/", "/aɪ/"],
            "completed": progress.get(5, {}).get("completed", False),
            "avg_score": progress.get(5, {}).get("avg_score", 0),
            "phrases_practiced": progress.get(5, {}).get("phrases_practiced", 0),
        },
        {
            "level": 6,
            "name": "Vocabulario británico",
            "phonemes": ["expressions", "pronunciation"],
            "completed": progress.get(6, {}).get("completed", False),
            "avg_score": progress.get(6, {}).get("avg_score", 0),
            "phrases_practiced": progress.get(6, {}).get("phrases_practiced", 0),
        },
    ]

    return levels

@router.get("/level/{level_id}/phrases")
def get_level_phrases(level_id: int, user_id: str, limit: int = 5):
    """
    Get phrases for a level, excluding recently practiced ones.
    """
    phrases = _load_phrases()
    level_phrases = [p for p in phrases.values() if p.get("level") == level_id]

    if not level_phrases:
        raise HTTPException(404, f"No phrases found for level {level_id}")

    # Get recently practiced phrase IDs (last 20)
    with get_connection(_get_db_path()) as conn:
        rows = conn.execute(
            """SELECT phrase_id FROM practice_history
               WHERE user_id = ? AND level = ?
               ORDER BY created_at DESC LIMIT 20""",
            (user_id, level_id)
        ).fetchall()

    recent_ids = {row["phrase_id"] for row in rows}

    # Filter out recent phrases
    available = [p for p in level_phrases if p["id"] not in recent_ids]

    # If all phrases have been practiced recently, reset
    if not available:
        available = level_phrases

    # Return up to limit phrases
    import random
    random.shuffle(available)
    return available[:limit]

@router.post("/assess")
async def assess_pronunciation(
    audio: UploadFile = File(...),
    phrase_id: int = Form(...),
    user_id: str = Form(...),
    attempt: int = Form(1),
):
    """
    Assess pronunciation and update user progress.
    """
    phrases = _load_phrases()
    if phrase_id not in phrases:
        raise HTTPException(404, "Phrase not found")

    phrase = phrases[phrase_id]
    level = phrase.get("level", 1)

    # Save audio to temp file
    content = await audio.read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(content)
        wav_path = tmp.name

    try:
        # Run Azure assessment
        azure_result = run_assessment(wav_path, phrase["en"])
    finally:
        os.unlink(wav_path)

    # Calculate strict score
    strict_score = calculate_strict_score(azure_result["words"])

    # Get phoneme scores
    phoneme_scores = get_phoneme_scores(azure_result["words"])

    # Get AI coaching
    coaching = get_coaching(phrase, azure_result["words"], attempt)

    # Save to practice history
    with get_connection(_get_db_path()) as conn:
        conn.execute(
            """INSERT INTO practice_history (user_id, phrase_id, level, score, word_scores)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, phrase_id, level, strict_score, json.dumps(azure_result["words"]))
        )

        # Update phoneme scores (running average)
        for phoneme, score in phoneme_scores.items():
            conn.execute(
                """INSERT INTO phoneme_scores (user_id, phoneme, score, sample_count)
                   VALUES (?, ?, ?, 1)
                   ON CONFLICT(user_id, phoneme) DO UPDATE SET
                   score = (score * sample_count + ?) / (sample_count + 1),
                   sample_count = sample_count + 1,
                   updated_at = CURRENT_TIMESTAMP""",
                (user_id, phoneme, score, score)
            )

        # Update level progress
        conn.execute(
            """INSERT INTO level_progress (user_id, level, avg_score, phrases_practiced)
               VALUES (?, ?, ?, 1)
               ON CONFLICT(user_id, level) DO UPDATE SET
               avg_score = (avg_score * phrases_practiced + ?) / (phrases_practiced + 1),
               phrases_practiced = phrases_practiced + 1,
               completed = CASE WHEN
                   (avg_score * phrases_practiced + ?) / (phrases_practiced + 1) >= 75
                   AND phrases_practiced >= 5
               THEN 1 ELSE completed END""",
            (user_id, level, strict_score, strict_score, strict_score)
        )

        conn.commit()

    return JSONResponse({
        "score": strict_score,
        "accuracy": azure_result["accuracy"],
        "fluency": azure_result["fluency"],
        "completeness": azure_result["completeness"],
        "transcription": azure_result["transcription"],
        "words": azure_result["words"],
        "phoneme_scores": phoneme_scores,
        "tips": coaching.get("tips", []),
        "focus": coaching.get("focus", phrase["notes"]),
        "encouragement": coaching.get("encouragement", ""),
    })
