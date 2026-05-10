import os
import json
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from database import get_connection
from services.azure_speech import run_assessment
from services.scoring import get_phoneme_scores, get_problem_areas

router = APIRouter(prefix="/api/diagnostic", tags=["diagnostic"])

def _get_db_path():
    return os.environ.get("TEST_DB_PATH") or None

def _load_diagnostic_data() -> dict:
    data_file = Path(__file__).parent.parent / "data" / "diagnostic.json"
    return json.loads(data_file.read_text())

@router.get("/phrases")
def get_diagnostic_phrases():
    """Get all diagnostic phrases and words."""
    return _load_diagnostic_data()

@router.post("/assess")
async def assess_diagnostic(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    part: str = Form(...),  # "minimal_pairs", "non_rhotic", or "paragraph"
):
    """
    Assess diagnostic audio and return phoneme analysis.
    """
    diag_data = _load_diagnostic_data()

    # Determine reference text based on part
    if part == "minimal_pairs":
        # All minimal pair words concatenated
        words = []
        for pair in diag_data["minimal_pairs"]:
            words.extend([pair["word1"], pair["word2"]])
        reference_text = " ".join(words)
    elif part == "non_rhotic":
        reference_text = " ".join(diag_data["non_rhotic_words"])
    elif part == "paragraph":
        reference_text = diag_data["diagnostic_paragraph"]["text"]
    else:
        raise HTTPException(400, f"Invalid part: {part}")

    # Save audio to temp file
    content = await audio.read()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(content)
        wav_path = tmp.name

    try:
        azure_result = run_assessment(wav_path, reference_text)
    finally:
        os.unlink(wav_path)

    phoneme_scores = get_phoneme_scores(azure_result["words"])

    return JSONResponse({
        "part": part,
        "transcription": azure_result["transcription"],
        "words": azure_result["words"],
        "phoneme_scores": phoneme_scores,
    })

@router.post("/complete")
async def complete_diagnostic(user_id: str = Form(...), phoneme_scores: str = Form(...)):
    """
    Save diagnostic results and mark diagnostic as complete.
    phoneme_scores should be JSON: {"θ": 65, "ð": 70, ...}
    """
    scores = json.loads(phoneme_scores)
    problem_areas = get_problem_areas(scores)

    # Determine recommended starting level based on problem areas
    recommended_level = 1  # Default

    # If /θ/ and /ð/ are good, move to level 2
    if scores.get("θ", 0) >= 75 and scores.get("ð", 0) >= 75:
        recommended_level = 2
        # If vowels are also good, move to level 3
        if all(scores.get(p, 0) >= 75 for p in ["ɪ", "æ", "ʌ"]):
            recommended_level = 3

    with get_connection(_get_db_path()) as conn:
        # Save phoneme scores
        for phoneme, score in scores.items():
            conn.execute(
                """INSERT INTO phoneme_scores (user_id, phoneme, score, sample_count)
                   VALUES (?, ?, ?, 1)
                   ON CONFLICT(user_id, phoneme) DO UPDATE SET
                   score = ?, sample_count = 1, updated_at = CURRENT_TIMESTAMP""",
                (user_id, phoneme, score, score)
            )

        # Mark diagnostic as complete
        conn.execute(
            "UPDATE users SET diagnostic_completed = TRUE WHERE id = ?",
            (user_id,)
        )

        conn.commit()

    return JSONResponse({
        "phoneme_scores": scores,
        "problem_areas": problem_areas,
        "recommended_level": recommended_level,
    })

@router.get("/results/{user_id}")
def get_diagnostic_results(user_id: str):
    """Get stored diagnostic results for a user."""
    with get_connection(_get_db_path()) as conn:
        # Check if diagnostic completed
        user_row = conn.execute(
            "SELECT diagnostic_completed FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if not user_row:
            raise HTTPException(404, "User not found")

        if not user_row["diagnostic_completed"]:
            raise HTTPException(404, "Diagnostic not completed")

        # Get phoneme scores
        rows = conn.execute(
            "SELECT phoneme, score FROM phoneme_scores WHERE user_id = ?",
            (user_id,)
        ).fetchall()

    phoneme_scores = {row["phoneme"]: row["score"] for row in rows}
    problem_areas = get_problem_areas(phoneme_scores)

    return {
        "phoneme_scores": phoneme_scores,
        "problem_areas": problem_areas,
    }
