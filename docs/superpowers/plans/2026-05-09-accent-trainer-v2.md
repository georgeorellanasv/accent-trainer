# Accent Trainer v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the MVP accent trainer into a complete pronunciation improvement system with diagnostic assessment, personalized journey map, visual waveform feedback, and persistent progress tracking.

**Architecture:** SQLite for persistence, FastAPI with routers for modular backend, Azure TTS Neural for consistent RP reference audio, Web Audio API + Canvas for waveform visualization. The existing MVP code will be refactored into a proper module structure.

**Tech Stack:** Python 3.9+, FastAPI, SQLite, Azure Speech SDK, Azure TTS, Cerebras (Llama 3.1), Web Audio API, Canvas

---

## File Structure Overview

```
accent-trainer/
├── server.py                 → Main FastAPI app (refactored)
├── database.py               → SQLite setup and connection
├── models.py                 → Pydantic models
├── routers/
│   ├── __init__.py
│   ├── user.py              → User profile endpoints
│   ├── diagnostic.py        → Diagnostic assessment endpoints
│   ├── practice.py          → Practice session endpoints
│   └── tts.py               → Azure TTS endpoints
├── services/
│   ├── __init__.py
│   ├── azure_speech.py      → Azure Pronunciation Assessment
│   ├── azure_tts.py         → Azure TTS Neural
│   ├── cerebras.py          → Coaching with Cerebras
│   └── scoring.py           → Strict scoring logic
├── static/
│   ├── index.html           → Main app (journey map + practice)
│   ├── diagnostic.html      → Diagnostic screen
│   ├── profile.html         → Profile setup
│   ├── css/
│   │   └── styles.css       → Shared styles
│   └── js/
│       ├── waveform.js      → Waveform visualization
│       ├── recorder.js      → Audio recording
│       └── app.js           → Main app logic
├── data/
│   ├── phrases_level_1.json → Level 1 phrases (30+)
│   ├── phrases_level_2.json → Level 2 phrases (30+)
│   ├── phrases_level_3.json → Level 3 phrases (30+)
│   ├── phrases_level_4.json → Level 4 phrases (30+)
│   ├── phrases_level_5.json → Level 5 phrases (30+)
│   ├── phrases_level_6.json → Level 6 phrases (30+)
│   ├── diagnostic.json      → Diagnostic phrases
│   └── accent-trainer.db    → SQLite database (generated)
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_user.py
│   ├── test_scoring.py
│   └── test_diagnostic.py
└── requirements.txt         → Updated dependencies
```

---

## Phase 1: Infrastructure

### Task 1: Update Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Update requirements.txt with new dependencies**

```txt
fastapi
uvicorn[standard]
azure-cognitiveservices-speech
openai
requests
python-multipart
python-dotenv
aiosqlite
pytest
pytest-asyncio
httpx
```

- [ ] **Step 2: Install new dependencies**

Run: `python3 -m pip install -r requirements.txt`
Expected: Successfully installed aiosqlite, pytest, pytest-asyncio, httpx

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add SQLite and testing dependencies"
```

---

### Task 2: Create Database Module

**Files:**
- Create: `database.py`
- Create: `tests/test_database.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create tests directory and init file**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 2: Write failing test for database initialization**

Create `tests/test_database.py`:

```python
import pytest
import os
import tempfile
from database import init_db, get_db_path, get_connection

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)

def test_init_db_creates_tables(temp_db):
    init_db(temp_db)
    import sqlite3
    conn = sqlite3.connect(temp_db)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    assert "users" in tables
    assert "phoneme_scores" in tables
    assert "practice_history" in tables
    assert "level_progress" in tables

def test_get_db_path_returns_data_directory():
    path = get_db_path()
    assert "data" in str(path)
    assert path.name == "accent-trainer.db"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m pytest tests/test_database.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'database'"

- [ ] **Step 4: Create database.py with schema**

Create `database.py`:

```python
import sqlite3
from pathlib import Path
from contextlib import contextmanager

def get_db_path() -> Path:
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "accent-trainer.db"

def init_db(db_path: str | Path | None = None) -> None:
    if db_path is None:
        db_path = get_db_path()
    
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            voice_preference TEXT DEFAULT 'female',
            onboarding_mode TEXT DEFAULT 'full',
            diagnostic_completed BOOLEAN DEFAULT FALSE
        );

        CREATE TABLE IF NOT EXISTS phoneme_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            phoneme TEXT NOT NULL,
            score REAL NOT NULL,
            sample_count INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, phoneme)
        );

        CREATE TABLE IF NOT EXISTS practice_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            phrase_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            score REAL NOT NULL,
            word_scores TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS level_progress (
            user_id TEXT NOT NULL,
            level INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            avg_score REAL DEFAULT 0,
            phrases_practiced INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, level),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

@contextmanager
def get_connection(db_path: str | Path | None = None):
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 -m pytest tests/test_database.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add database.py tests/
git commit -m "feat: add SQLite database module with schema"
```

---

### Task 3: Create Pydantic Models

**Files:**
- Create: `models.py`

- [ ] **Step 1: Create models.py with all data models**

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid

class UserCreate(BaseModel):
    voice_preference: Literal["male", "female"] = "female"
    onboarding_mode: Literal["full", "gradual"] = "full"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: Optional[datetime] = None
    voice_preference: Literal["male", "female"] = "female"
    onboarding_mode: Literal["full", "gradual"] = "full"
    diagnostic_completed: bool = False

class UserUpdate(BaseModel):
    voice_preference: Optional[Literal["male", "female"]] = None
    onboarding_mode: Optional[Literal["full", "gradual"]] = None
    diagnostic_completed: Optional[bool] = None

class PhonemeScore(BaseModel):
    phoneme: str
    score: float
    sample_count: int = 1

class PracticeResult(BaseModel):
    phrase_id: int
    level: int
    score: float
    word_scores: list[dict]

class LevelProgress(BaseModel):
    level: int
    completed: bool = False
    avg_score: float = 0.0
    phrases_practiced: int = 0

class DiagnosticResult(BaseModel):
    phoneme_scores: list[PhonemeScore]
    problem_areas: list[str]
    recommended_level: int

class Phrase(BaseModel):
    id: int
    en: str
    ipa_rp: str
    target_phonemes: list[str]
    difficulty: Literal["easy", "medium", "hard"]
    notes: str
    es: Optional[str] = None

class AssessmentRequest(BaseModel):
    phrase_id: int
    attempt: int = 1

class AssessmentResponse(BaseModel):
    score: float
    accuracy: float
    fluency: float
    completeness: float
    transcription: str
    words: list[dict]
    tips: list[dict]
    focus: str
    encouragement: str
```

- [ ] **Step 2: Verify models import correctly**

Run: `python3 -c "from models import User, Phrase, AssessmentResponse; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add models.py
git commit -m "feat: add Pydantic models for API"
```

---

### Task 4: Create Directory Structure

**Files:**
- Create: `routers/__init__.py`
- Create: `services/__init__.py`
- Create: `static/css/styles.css`
- Create: `static/js/app.js`
- Create: `data/` directory

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p routers services static/css static/js data
touch routers/__init__.py services/__init__.py
```

- [ ] **Step 2: Create placeholder CSS file**

Create `static/css/styles.css`:

```css
:root {
  --paper:  #F5F4EE;
  --ink:    #1F1D1B;
  --clay:   #CC785C;
  --clay-d: #A1543D;
  --sand:   #EBE5D7;
  --border: rgba(20,20,19,0.12);
  --ok:     #4A7C59;
  --warn:   #B8860B;
  --err:    #CC785C;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: Inter, -apple-system, sans-serif;
  font-size: 14px;
  background: var(--paper);
  color: var(--ink);
  min-height: 100vh;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 16px;
}

.card-header {
  background: var(--sand);
  padding: 12px 18px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.card-body {
  padding: 18px;
}

.btn {
  cursor: pointer;
  border: none;
  border-radius: 7px;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 10px 18px;
  transition: all 0.15s;
}

.btn-primary {
  background: var(--clay);
  color: white;
}

.btn-primary:hover {
  background: var(--clay-d);
}

.btn-secondary {
  background: var(--sand);
  color: var(--ink);
  border: 1px solid var(--border);
}

.waveform-container {
  display: flex;
  gap: 20px;
  margin: 20px 0;
}

.waveform-box {
  flex: 1;
  background: var(--sand);
  border-radius: 8px;
  padding: 15px;
}

.waveform-box canvas {
  width: 100%;
  height: 100px;
  background: white;
  border-radius: 4px;
}

.waveform-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 8px;
  opacity: 0.7;
}

.phoneme-heatmap {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
  margin: 20px 0;
}

.phoneme-cell {
  padding: 12px 8px;
  border-radius: 6px;
  text-align: center;
  font-family: monospace;
}

.phoneme-cell.good { background: rgba(74,124,89,0.2); }
.phoneme-cell.warn { background: rgba(184,134,11,0.2); }
.phoneme-cell.bad { background: rgba(204,120,92,0.2); }

.level-card {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.level-card:hover {
  border-color: var(--clay);
}

.level-card.locked {
  opacity: 0.5;
  cursor: not-allowed;
}

.level-card.completed {
  border-color: var(--ok);
}

.level-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--clay);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  margin-right: 16px;
}

.level-card.completed .level-number {
  background: var(--ok);
}

.progress-bar {
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
  margin-top: 8px;
}

.progress-fill {
  height: 100%;
  background: var(--clay);
  border-radius: 3px;
  transition: width 0.3s;
}
```

- [ ] **Step 3: Commit**

```bash
git add routers/ services/ static/ data/
git commit -m "chore: create directory structure for v2"
```

---

## Phase 2: Services Layer

### Task 5: Extract Azure Speech Service

**Files:**
- Create: `services/azure_speech.py`
- Modify: `server.py` (extract function)

- [ ] **Step 1: Create azure_speech.py service**

Create `services/azure_speech.py`:

```python
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
```

- [ ] **Step 2: Verify import works**

Run: `python3 -c "from services.azure_speech import run_assessment; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add services/azure_speech.py
git commit -m "refactor: extract Azure Speech service"
```

---

### Task 6: Create Azure TTS Service

**Files:**
- Create: `services/azure_tts.py`

- [ ] **Step 1: Create azure_tts.py service**

Create `services/azure_tts.py`:

```python
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
```

- [ ] **Step 2: Verify import works**

Run: `python3 -c "from services.azure_tts import get_tts_audio; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add services/azure_tts.py
git commit -m "feat: add Azure TTS Neural service with caching"
```

---

### Task 7: Create Scoring Service

**Files:**
- Create: `services/scoring.py`
- Create: `tests/test_scoring.py`

- [ ] **Step 1: Write failing test for strict scoring**

Create `tests/test_scoring.py`:

```python
import pytest
from services.scoring import calculate_strict_score, get_phoneme_scores

def test_calculate_strict_score_perfect():
    word_scores = [
        {"word": "think", "accuracy": 95, "phonemes": [{"phoneme": "θ", "accuracy": 95}]},
        {"word": "the", "accuracy": 92, "phonemes": [{"phoneme": "ð", "accuracy": 92}]},
    ]
    score = calculate_strict_score(word_scores)
    assert score >= 9.0

def test_calculate_strict_score_poor_th():
    word_scores = [
        {"word": "think", "accuracy": 50, "phonemes": [{"phoneme": "θ", "accuracy": 40}]},
        {"word": "the", "accuracy": 88, "phonemes": [{"phoneme": "ð", "accuracy": 88}]},
    ]
    score = calculate_strict_score(word_scores)
    assert score < 7.0  # Penalized for poor /θ/

def test_get_phoneme_scores_extracts_all():
    word_scores = [
        {"word": "think", "phonemes": [{"phoneme": "θ", "accuracy": 80}, {"phoneme": "ɪ", "accuracy": 90}]},
        {"word": "the", "phonemes": [{"phoneme": "ð", "accuracy": 70}]},
    ]
    result = get_phoneme_scores(word_scores)
    assert result["θ"] == 80
    assert result["ð"] == 70
    assert result["ɪ"] == 90
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_scoring.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create scoring.py service**

Create `services/scoring.py`:

```python
# Key RP phonemes that get extra weight in scoring
RP_KEY_PHONEMES = {"θ", "ð", "ɑː", "ɔː", "əʊ", "ɪ", "æ", "ʌ", "ə"}

# Phonemes that Spanish speakers struggle with most
PROBLEM_PHONEMES = {"θ", "ð"}  # Extra penalty for these

def calculate_strict_score(word_scores: list[dict]) -> float:
    """
    Calculate a strict 0-10 score from Azure word scores.
    Applies extra penalties for RP-critical phonemes.
    """
    if not word_scores:
        return 0.0

    total_weight = 0
    weighted_score = 0

    for word in word_scores:
        word_acc = word.get("accuracy", 0)
        phonemes = word.get("phonemes", [])
        
        # Base weight for word
        weight = 1.0
        
        # Check for problem phonemes
        for p in phonemes:
            phoneme = p.get("phoneme", "")
            p_acc = p.get("accuracy", 0)
            
            if phoneme in PROBLEM_PHONEMES:
                # Double weight for /θ/ and /ð/
                weight += 1.0
                # Extra penalty if they're bad
                if p_acc < 60:
                    word_acc = min(word_acc, p_acc * 0.8)
            elif phoneme in RP_KEY_PHONEMES:
                weight += 0.5

        weighted_score += word_acc * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    # Convert 0-100 to 0-10 scale
    raw_score = weighted_score / total_weight
    
    # Apply strictness curve (makes it harder to get high scores)
    # 100 -> 10, 90 -> 8.5, 80 -> 7, 70 -> 5.5, 60 -> 4
    strict_score = (raw_score / 100) * 10
    if raw_score < 90:
        strict_score -= (90 - raw_score) * 0.05
    
    return max(0, min(10, round(strict_score, 1)))


def get_phoneme_scores(word_scores: list[dict]) -> dict[str, float]:
    """
    Extract individual phoneme scores from word scores.
    Returns dict mapping phoneme -> score
    """
    phoneme_scores = {}
    phoneme_counts = {}
    
    for word in word_scores:
        for p in word.get("phonemes", []):
            phoneme = p.get("phoneme", "")
            accuracy = p.get("accuracy", 0)
            
            if phoneme not in phoneme_scores:
                phoneme_scores[phoneme] = 0
                phoneme_counts[phoneme] = 0
            
            phoneme_scores[phoneme] += accuracy
            phoneme_counts[phoneme] += 1
    
    # Average scores
    for phoneme in phoneme_scores:
        if phoneme_counts[phoneme] > 0:
            phoneme_scores[phoneme] = round(
                phoneme_scores[phoneme] / phoneme_counts[phoneme], 1
            )
    
    return phoneme_scores


def get_problem_areas(phoneme_scores: dict[str, float], threshold: float = 75) -> list[str]:
    """
    Return list of phonemes below threshold, sorted by severity.
    """
    problems = [
        (phoneme, score) 
        for phoneme, score in phoneme_scores.items() 
        if score < threshold
    ]
    problems.sort(key=lambda x: x[1])  # Worst first
    return [p[0] for p in problems]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_scoring.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add services/scoring.py tests/test_scoring.py
git commit -m "feat: add strict scoring service with RP phoneme weighting"
```

---

### Task 8: Extract Cerebras Service

**Files:**
- Create: `services/cerebras.py`

- [ ] **Step 1: Create cerebras.py service**

Create `services/cerebras.py`:

```python
import os
import json
from openai import OpenAI
from fastapi import HTTPException

COACHING_SYSTEM = """You are a strict RP (Received Pronunciation) accent coach for Latin American Spanish speakers.
You receive Azure Pronunciation Assessment data with exact scores per word and phoneme.
Give specific, actionable tips for words that scored below 75. Be honest and direct.

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
Keep tips under 25 words each. Be warm but precise and honest."""


def get_client() -> OpenAI:
    key = os.environ.get("CEREBRAS_API_KEY", "")
    if not key:
        raise HTTPException(503, "CEREBRAS_API_KEY not configured")
    return OpenAI(base_url="https://api.cerebras.ai/v1", api_key=key)


def get_coaching(phrase: dict, word_scores: list, attempt: int) -> dict:
    """
    Get AI coaching feedback based on pronunciation assessment.
    """
    try:
        client = get_client()
        problem_words = [w for w in word_scores if w["accuracy"] < 75]
        
        user_msg = (
            f'Phrase: "{phrase["en"]}"\n'
            f'IPA RP: {phrase["ipa_rp"]}\n'
            f'Target phonemes: {", ".join(phrase.get("target_phonemes", []))}\n'
            f'Attempt #{attempt}\n\n'
            f'Word scores (Azure):\n' +
            "\n".join(
                f'  {w["word"]}: {w["accuracy"]:.0f}/100'
                + (f' — worst phoneme: /{w["worst_phoneme"]}/ ({w["worst_phoneme_score"]:.0f}/100)' 
                   if w.get("worst_phoneme") else "")
                for w in word_scores
            ) +
            f'\n\nProblem words: {[w["word"] for w in problem_words]}'
        )
        
        resp = client.chat.completions.create(
            model="llama3.1-8b",
            max_tokens=512,
            messages=[
                {"role": "system", "content": COACHING_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
        )
        
        raw = resp.choices[0].message.content.strip()
        
        # Handle markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        return json.loads(raw.strip())
        
    except json.JSONDecodeError:
        return {
            "tips": [],
            "focus": phrase.get("notes", "Focus on the target phonemes."),
            "encouragement": "Keep practising — every attempt counts!",
        }
    except Exception:
        return {
            "tips": [],
            "focus": phrase.get("notes", "Focus on the target phonemes."),
            "encouragement": "Keep practising — every attempt counts!",
        }
```

- [ ] **Step 2: Verify import works**

Run: `python3 -c "from services.cerebras import get_coaching; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add services/cerebras.py
git commit -m "refactor: extract Cerebras coaching service"
```

---

## Phase 3: API Routers

### Task 9: Create User Router

**Files:**
- Create: `routers/user.py`
- Create: `tests/test_user.py`

- [ ] **Step 1: Write failing test for user endpoints**

Create `tests/test_user.py`:

```python
import pytest
from fastapi.testclient import TestClient
import tempfile
import os

# Setup test database
@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TEST_DB_PATH", path)
    
    from database import init_db
    init_db(path)
    
    yield path
    os.unlink(path)

@pytest.fixture
def client(setup_test_db):
    # Import after setting up test db
    from server import app
    return TestClient(app)

def test_create_user(client):
    response = client.post("/api/user", json={
        "voice_preference": "male",
        "onboarding_mode": "full"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["voice_preference"] == "male"
    assert data["onboarding_mode"] == "full"
    assert "id" in data

def test_get_user(client):
    # Create user first
    create_resp = client.post("/api/user", json={"voice_preference": "female"})
    user_id = create_resp.json()["id"]
    
    # Get user
    response = client.get(f"/api/user/{user_id}")
    assert response.status_code == 200
    assert response.json()["id"] == user_id

def test_update_user(client):
    # Create user first
    create_resp = client.post("/api/user", json={"voice_preference": "female"})
    user_id = create_resp.json()["id"]
    
    # Update user
    response = client.put(f"/api/user/{user_id}", json={"voice_preference": "male"})
    assert response.status_code == 200
    assert response.json()["voice_preference"] == "male"
```

- [ ] **Step 2: Create user router**

Create `routers/user.py`:

```python
import os
from fastapi import APIRouter, HTTPException
from models import User, UserCreate, UserUpdate
from database import get_connection

router = APIRouter(prefix="/api/user", tags=["user"])

def _get_db_path():
    return os.environ.get("TEST_DB_PATH") or None

@router.post("", response_model=User)
def create_user(user_data: UserCreate):
    user = User(
        voice_preference=user_data.voice_preference,
        onboarding_mode=user_data.onboarding_mode
    )
    
    with get_connection(_get_db_path()) as conn:
        conn.execute(
            """INSERT INTO users (id, voice_preference, onboarding_mode) 
               VALUES (?, ?, ?)""",
            (user.id, user.voice_preference, user.onboarding_mode)
        )
        conn.commit()
    
    return user

@router.get("/{user_id}", response_model=User)
def get_user(user_id: str):
    with get_connection(_get_db_path()) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    
    if not row:
        raise HTTPException(404, "User not found")
    
    return User(
        id=row["id"],
        created_at=row["created_at"],
        voice_preference=row["voice_preference"],
        onboarding_mode=row["onboarding_mode"],
        diagnostic_completed=bool(row["diagnostic_completed"])
    )

@router.put("/{user_id}", response_model=User)
def update_user(user_id: str, update: UserUpdate):
    with get_connection(_get_db_path()) as conn:
        # Check user exists
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(404, "User not found")
        
        # Build update query
        updates = []
        values = []
        
        if update.voice_preference is not None:
            updates.append("voice_preference = ?")
            values.append(update.voice_preference)
        if update.onboarding_mode is not None:
            updates.append("onboarding_mode = ?")
            values.append(update.onboarding_mode)
        if update.diagnostic_completed is not None:
            updates.append("diagnostic_completed = ?")
            values.append(update.diagnostic_completed)
        
        if updates:
            values.append(user_id)
            conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                values
            )
            conn.commit()
        
        # Return updated user
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    
    return User(
        id=row["id"],
        created_at=row["created_at"],
        voice_preference=row["voice_preference"],
        onboarding_mode=row["onboarding_mode"],
        diagnostic_completed=bool(row["diagnostic_completed"])
    )
```

- [ ] **Step 3: Commit (tests will pass after server.py is updated)**

```bash
git add routers/user.py tests/test_user.py
git commit -m "feat: add user router with CRUD endpoints"
```

---

### Task 10: Create TTS Router

**Files:**
- Create: `routers/tts.py`

- [ ] **Step 1: Create TTS router**

Create `routers/tts.py`:

```python
import os
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

def _get_phrase_text(phrase_id: int) -> str | None:
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
```

- [ ] **Step 2: Verify import works**

Run: `python3 -c "from routers.tts import router; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add routers/tts.py
git commit -m "feat: add TTS router with Azure Neural voices"
```

---

### Task 11: Create Practice Router

**Files:**
- Create: `routers/practice.py`

- [ ] **Step 1: Create practice router**

Create `routers/practice.py`:

```python
import os
import json
import tempfile
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
_phrases_cache: dict[int, dict] = {}

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
```

- [ ] **Step 2: Verify import works**

Run: `python3 -c "from routers.practice import router; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add routers/practice.py
git commit -m "feat: add practice router with level progress tracking"
```

---

### Task 12: Create Diagnostic Router

**Files:**
- Create: `routers/diagnostic.py`
- Create: `data/diagnostic.json`

- [ ] **Step 1: Create diagnostic phrases JSON**

Create `data/diagnostic.json`:

```json
{
  "minimal_pairs": [
    {"id": 1001, "word1": "think", "word2": "sink", "target": "θ"},
    {"id": 1002, "word1": "ship", "word2": "sheep", "target": "ɪ/iː"},
    {"id": 1003, "word1": "cat", "word2": "cut", "target": "æ/ʌ"},
    {"id": 1004, "word1": "path", "word2": "pat", "target": "ɑː"},
    {"id": 1005, "word1": "three", "word2": "tree", "target": "θ"},
    {"id": 1006, "word1": "this", "word2": "dis", "target": "ð"}
  ],
  "non_rhotic_words": ["water", "rather", "father", "better"],
  "diagnostic_paragraph": {
    "text": "I think the weather in the north of England is rather different from what we're used to. The path through the park looks absolutely marvellous in spring. Would you be so kind as to pass the water? I suppose we shall have to leave rather early this afternoon.",
    "target_phonemes": ["θ", "ð", "ɑː", "ɔː", "ɪ", "iː", "æ", "ʌ", "əʊ", "ə"],
    "ipa": "/aɪ θɪŋk ðə ˈweðə ɪn ðə nɔːθ əv ˈɪŋɡlənd ɪz ˈrɑːðə ˈdɪfrənt frəm wɒt wɪə ˈjuːst tuː. ðə pɑːθ θruː ðə pɑːk lʊks ˈæbsəluːtli ˈmɑːvələs ɪn sprɪŋ. wʊd juː biː səʊ kaɪnd æz tə pɑːs ðə ˈwɔːtə? aɪ səˈpəʊz wiː ʃæl hæv tə liːv ˈrɑːðə ˈɜːli ðɪs ˌɑːftəˈnuːn./"
  }
}
```

- [ ] **Step 2: Create diagnostic router**

Create `routers/diagnostic.py`:

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add routers/diagnostic.py data/diagnostic.json
git commit -m "feat: add diagnostic router with phoneme analysis"
```

---

### Task 13: Refactor Main Server

**Files:**
- Modify: `server.py`

- [ ] **Step 1: Refactor server.py to use routers**

Replace `server.py` with:

```python
import os
import ssl
from pathlib import Path
from contextlib import asynccontextmanager

# Corporate SSL bypass
ssl._create_default_https_context = ssl._create_unverified_context
os.environ.setdefault("CURL_CA_BUNDLE", "")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "")

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_db
from routers import user, tts, practice, diagnostic

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    yield

app = FastAPI(title="Accent Trainer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Include routers
app.include_router(user.router)
app.include_router(tts.router)
app.include_router(practice.router)
app.include_router(diagnostic.router)

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve main app
@app.get("/")
def serve_app():
    # Check for new static/index.html first, fall back to legacy app.html
    new_index = Path(__file__).parent / "static" / "index.html"
    legacy_index = Path(__file__).parent / "app.html"
    
    if new_index.exists():
        return FileResponse(new_index)
    elif legacy_index.exists():
        return FileResponse(legacy_index)
    else:
        return {"message": "Accent Trainer API", "docs": "/docs"}

@app.get("/diagnostic")
def serve_diagnostic():
    return FileResponse(Path(__file__).parent / "static" / "diagnostic.html")

@app.get("/profile")
def serve_profile():
    return FileResponse(Path(__file__).parent / "static" / "profile.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8001, reload=True)
```

- [ ] **Step 2: Verify server starts**

Run: `cd /Users/georgeorellanasv/accent-trainer && python3 -c "from server import app; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add server.py
git commit -m "refactor: modularize server with routers and lifespan"
```

---

## Phase 4: Frontend

### Task 14: Create Waveform Visualization

**Files:**
- Create: `static/js/waveform.js`

- [ ] **Step 1: Create waveform.js**

Create `static/js/waveform.js`:

```javascript
class WaveformVisualizer {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.options = {
      barColor: options.barColor || '#CC785C',
      barWidth: options.barWidth || 3,
      barGap: options.barGap || 1,
      backgroundColor: options.backgroundColor || '#FFFFFF',
      ...options
    };
    this.audioData = null;
  }

  async loadAudio(audioBlob) {
    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioContext = new AudioContext();
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    this.audioData = audioBuffer.getChannelData(0);
    await audioContext.close();
    this.draw();
  }

  async loadFromUrl(url) {
    const response = await fetch(url);
    const blob = await response.blob();
    await this.loadAudio(blob);
  }

  draw() {
    if (!this.audioData) return;

    const { width, height } = this.canvas;
    const { barColor, barWidth, barGap, backgroundColor } = this.options;

    // Clear canvas
    this.ctx.fillStyle = backgroundColor;
    this.ctx.fillRect(0, 0, width, height);

    // Calculate bars
    const totalBars = Math.floor(width / (barWidth + barGap));
    const samplesPerBar = Math.floor(this.audioData.length / totalBars);

    this.ctx.fillStyle = barColor;

    for (let i = 0; i < totalBars; i++) {
      // Get average amplitude for this bar
      let sum = 0;
      const start = i * samplesPerBar;
      for (let j = 0; j < samplesPerBar; j++) {
        sum += Math.abs(this.audioData[start + j] || 0);
      }
      const avg = sum / samplesPerBar;

      // Scale to canvas height
      const barHeight = Math.max(2, avg * height * 2);
      const x = i * (barWidth + barGap);
      const y = (height - barHeight) / 2;

      // Draw rounded bar
      this.ctx.beginPath();
      this.ctx.roundRect(x, y, barWidth, barHeight, barWidth / 2);
      this.ctx.fill();
    }
  }

  clear() {
    const { width, height } = this.canvas;
    this.ctx.fillStyle = this.options.backgroundColor;
    this.ctx.fillRect(0, 0, width, height);
    this.audioData = null;
  }
}

// Audio recorder with waveform
class AudioRecorder {
  constructor(options = {}) {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;
    this.onDataAvailable = options.onDataAvailable || (() => {});
    this.onStop = options.onStop || (() => {});
  }

  async start() {
    this.audioChunks = [];
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus' 
      : 'audio/webm';
    
    this.mediaRecorder = new MediaRecorder(this.stream, { mimeType });
    
    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        this.audioChunks.push(e.data);
        this.onDataAvailable(e.data);
      }
    };
    
    this.mediaRecorder.onstop = () => {
      const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
      this.onStop(blob);
    };
    
    this.mediaRecorder.start(100);
  }

  stop() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
    }
  }

  isRecording() {
    return this.mediaRecorder && this.mediaRecorder.state === 'recording';
  }
}

// Convert webm to wav for Azure
async function convertToWav(webmBlob) {
  const arrayBuffer = await webmBlob.arrayBuffer();
  const audioCtx = new AudioContext();
  const decoded = await audioCtx.decodeAudioData(arrayBuffer);
  await audioCtx.close();

  // Resample to 16kHz mono
  const targetRate = 16000;
  const offCtx = new OfflineAudioContext(
    1, 
    Math.ceil(decoded.duration * targetRate), 
    targetRate
  );
  const src = offCtx.createBufferSource();
  src.buffer = decoded;
  src.connect(offCtx.destination);
  src.start();
  const resampled = await offCtx.startRendering();

  const samples = resampled.getChannelData(0);
  const pcm = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    pcm[i] = Math.max(-32768, Math.min(32767, samples[i] * 32768));
  }

  // Create WAV
  const wavBuf = new ArrayBuffer(44 + pcm.buffer.byteLength);
  const v = new DataView(wavBuf);
  const writeStr = (off, s) => [...s].forEach((c, i) => v.setUint8(off + i, c.charCodeAt(0)));
  
  writeStr(0, 'RIFF');
  v.setUint32(4, 36 + pcm.buffer.byteLength, true);
  writeStr(8, 'WAVE');
  writeStr(12, 'fmt ');
  v.setUint32(16, 16, true);
  v.setUint16(20, 1, true);
  v.setUint16(22, 1, true);
  v.setUint32(24, targetRate, true);
  v.setUint32(28, targetRate * 2, true);
  v.setUint16(32, 2, true);
  v.setUint16(34, 16, true);
  writeStr(36, 'data');
  v.setUint32(40, pcm.buffer.byteLength, true);
  new Int16Array(wavBuf, 44).set(pcm);

  return new Blob([wavBuf], { type: 'audio/wav' });
}

// Export for use
window.WaveformVisualizer = WaveformVisualizer;
window.AudioRecorder = AudioRecorder;
window.convertToWav = convertToWav;
```

- [ ] **Step 2: Commit**

```bash
git add static/js/waveform.js
git commit -m "feat: add waveform visualization and audio recorder"
```

---

### Task 15: Create Profile Page

**Files:**
- Create: `static/profile.html`

- [ ] **Step 1: Create profile.html**

Create `static/profile.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Profile Setup - Accent Trainer</title>
  <link rel="stylesheet" href="/static/css/styles.css">
  <style>
    .setup-container {
      max-width: 500px;
      margin: 60px auto;
      padding: 20px;
    }
    .setup-title {
      font-size: 24px;
      font-weight: 700;
      margin-bottom: 8px;
    }
    .setup-subtitle {
      color: #666;
      margin-bottom: 32px;
    }
    .option-group {
      margin-bottom: 32px;
    }
    .option-label {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 12px;
      display: block;
    }
    .voice-options {
      display: flex;
      gap: 16px;
    }
    .voice-option {
      flex: 1;
      padding: 20px;
      border: 2px solid var(--border);
      border-radius: 12px;
      cursor: pointer;
      text-align: center;
      transition: all 0.15s;
    }
    .voice-option:hover {
      border-color: var(--clay);
    }
    .voice-option.selected {
      border-color: var(--clay);
      background: rgba(204, 120, 92, 0.1);
    }
    .voice-icon {
      font-size: 32px;
      margin-bottom: 8px;
    }
    .voice-name {
      font-weight: 600;
      margin-bottom: 4px;
    }
    .voice-desc {
      font-size: 12px;
      color: #666;
    }
    .mode-options {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .mode-option {
      padding: 16px;
      border: 2px solid var(--border);
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .mode-option:hover {
      border-color: var(--clay);
    }
    .mode-option.selected {
      border-color: var(--clay);
      background: rgba(204, 120, 92, 0.1);
    }
    .mode-title {
      font-weight: 600;
      margin-bottom: 4px;
    }
    .mode-desc {
      font-size: 13px;
      color: #666;
    }
    .start-btn {
      width: 100%;
      padding: 16px;
      font-size: 16px;
      margin-top: 20px;
    }
  </style>
</head>
<body>
  <div class="setup-container">
    <h1 class="setup-title">Welcome to Accent Trainer</h1>
    <p class="setup-subtitle">Let's set up your profile to get started with RP British pronunciation.</p>

    <div class="option-group">
      <label class="option-label">Choose your reference voice</label>
      <div class="voice-options">
        <div class="voice-option selected" data-voice="female" onclick="selectVoice('female')">
          <div class="voice-icon">👩</div>
          <div class="voice-name">Sonia</div>
          <div class="voice-desc">Female RP voice</div>
        </div>
        <div class="voice-option" data-voice="male" onclick="selectVoice('male')">
          <div class="voice-icon">👨</div>
          <div class="voice-name">Ryan</div>
          <div class="voice-desc">Male RP voice</div>
        </div>
      </div>
    </div>

    <div class="option-group">
      <label class="option-label">How would you like to start?</label>
      <div class="mode-options">
        <div class="mode-option selected" data-mode="full" onclick="selectMode('full')">
          <div class="mode-title">Full Diagnostic (Recommended)</div>
          <div class="mode-desc">Take a 90-second diagnostic to identify your specific pronunciation challenges. Get a personalized learning path.</div>
        </div>
        <div class="mode-option" data-mode="gradual" onclick="selectMode('gradual')">
          <div class="mode-title">Start Practicing</div>
          <div class="mode-desc">Jump right in. The system will learn your profile as you practice.</div>
        </div>
      </div>
    </div>

    <button class="btn btn-primary start-btn" onclick="startTraining()">
      Continue
    </button>
  </div>

  <script>
    let selectedVoice = 'female';
    let selectedMode = 'full';

    function selectVoice(voice) {
      selectedVoice = voice;
      document.querySelectorAll('.voice-option').forEach(el => {
        el.classList.toggle('selected', el.dataset.voice === voice);
      });
    }

    function selectMode(mode) {
      selectedMode = mode;
      document.querySelectorAll('.mode-option').forEach(el => {
        el.classList.toggle('selected', el.dataset.mode === mode);
      });
    }

    async function startTraining() {
      // Create user profile
      const response = await fetch('/api/user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          voice_preference: selectedVoice,
          onboarding_mode: selectedMode
        })
      });

      const user = await response.json();
      
      // Store user ID
      localStorage.setItem('userId', user.id);
      localStorage.setItem('voicePreference', selectedVoice);

      // Navigate based on mode
      if (selectedMode === 'full') {
        window.location.href = '/diagnostic';
      } else {
        window.location.href = '/';
      }
    }

    // Check if user already exists
    const existingUserId = localStorage.getItem('userId');
    if (existingUserId) {
      // Could add option to continue or start fresh
    }
  </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add static/profile.html
git commit -m "feat: add profile setup page"
```

---

### Task 16: Create Level 1 Phrases

**Files:**
- Create: `data/phrases_level_1.json`

- [ ] **Step 1: Create phrases_level_1.json with 30+ phrases**

Create `data/phrases_level_1.json`:

```json
[
  {
    "id": 101,
    "en": "I think the weather is rather dreadful today.",
    "ipa_rp": "/aɪ θɪŋk ðə ˈweðə ɪz ˈrɑːðə ˈdredf(ə)l təˈdeɪ/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "easy",
    "notes": "Focus on /θ/ in 'think' and /ð/ in 'the', 'weather', 'rather'."
  },
  {
    "id": 102,
    "en": "This is the third thing I thought about.",
    "ipa_rp": "/ðɪs ɪz ðə θɜːd θɪŋ aɪ θɔːt əˈbaʊt/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "Multiple /θ/ sounds: 'third', 'thing', 'thought'. /ð/ in 'this', 'the'."
  },
  {
    "id": 103,
    "en": "They think that those things are theirs.",
    "ipa_rp": "/ðeɪ θɪŋk ðæt ðəʊz θɪŋz ɑː ðeəz/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "hard",
    "notes": "Alternating /ð/ and /θ/ throughout. Challenging rhythm."
  },
  {
    "id": 104,
    "en": "Thank you for everything.",
    "ipa_rp": "/θæŋk juː fər ˈevrɪθɪŋ/",
    "target_phonemes": ["θ"],
    "difficulty": "easy",
    "notes": "Common phrase. /θ/ at start and end."
  },
  {
    "id": 105,
    "en": "The theatre is through that path.",
    "ipa_rp": "/ðə ˈθɪətə ɪz θruː ðæt pɑːθ/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'theatre', 'through', 'path'. /ð/ in 'the', 'that'."
  },
  {
    "id": 106,
    "en": "Nothing is worth more than health.",
    "ipa_rp": "/ˈnʌθɪŋ ɪz wɜːθ mɔː ðən helθ/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'nothing', 'worth', 'health'. /ð/ in 'than'."
  },
  {
    "id": 107,
    "en": "Both brothers think alike.",
    "ipa_rp": "/bəʊθ ˈbrʌðəz θɪŋk əˈlaɪk/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'both', 'think'. /ð/ in 'brothers'."
  },
  {
    "id": 108,
    "en": "There are three thousand people there.",
    "ipa_rp": "/ðeər ɑː θriː ˈθaʊzənd ˈpiːp(ə)l ðeə/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'three', 'thousand'. /ð/ in 'there' (appears twice)."
  },
  {
    "id": 109,
    "en": "I gather they're rather wealthy.",
    "ipa_rp": "/aɪ ˈɡæðə ðeə ˈrɑːðə ˈwelθi/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/ð/ in 'gather', 'they're', 'rather'. /θ/ in 'wealthy'."
  },
  {
    "id": 110,
    "en": "Breathe deeply through your mouth.",
    "ipa_rp": "/briːð ˈdiːpli θruː jɔː maʊθ/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/ð/ in 'breathe'. /θ/ in 'through', 'mouth'."
  },
  {
    "id": 111,
    "en": "Father thinks mother is right.",
    "ipa_rp": "/ˈfɑːðə θɪŋks ˈmʌðə ɪz raɪt/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "easy",
    "notes": "/ð/ in 'father', 'mother'. /θ/ in 'thinks'."
  },
  {
    "id": 112,
    "en": "The youth of today think differently.",
    "ipa_rp": "/ðə juːθ əv təˈdeɪ θɪŋk ˈdɪfrəntli/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'youth', 'think'. /ð/ in 'the'."
  },
  {
    "id": 113,
    "en": "Throw the cloth over there.",
    "ipa_rp": "/θrəʊ ðə klɒθ ˈəʊvə ðeə/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'throw', 'cloth'. /ð/ in 'the', 'there'."
  },
  {
    "id": 114,
    "en": "Thursday is the thirteenth.",
    "ipa_rp": "/ˈθɜːzdeɪ ɪz ðə ˌθɜːˈtiːnθ/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "hard",
    "notes": "Multiple /θ/ sounds. 'Thirteenth' has /θ/ twice."
  },
  {
    "id": 115,
    "en": "Think about the other method.",
    "ipa_rp": "/θɪŋk əˈbaʊt ði ˈʌðə ˈmeθəd/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'think', 'method'. /ð/ in 'the', 'other'."
  },
  {
    "id": 116,
    "en": "With this and that, the path is smooth.",
    "ipa_rp": "/wɪð ðɪs ənd ðæt ðə pɑːθ ɪz smuːð/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "hard",
    "notes": "/ð/ throughout. /θ/ in 'path'. /ð/ at end of 'smooth'."
  },
  {
    "id": 117,
    "en": "The truth is worth something.",
    "ipa_rp": "/ðə truːθ ɪz wɜːθ ˈsʌmθɪŋ/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'truth', 'worth', 'something'. /ð/ in 'the'."
  },
  {
    "id": 118,
    "en": "Gather your things together.",
    "ipa_rp": "/ˈɡæðə jɔː θɪŋz təˈɡeðə/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/ð/ in 'gather', 'together'. /θ/ in 'things'."
  },
  {
    "id": 119,
    "en": "Thick leather is worth the price.",
    "ipa_rp": "/θɪk ˈleðə ɪz wɜːθ ðə praɪs/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'thick', 'worth'. /ð/ in 'leather', 'the'."
  },
  {
    "id": 120,
    "en": "I thought the weather would be rather nice.",
    "ipa_rp": "/aɪ θɔːt ðə ˈweðə wʊd bi ˈrɑːðə naɪs/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'thought'. /ð/ in 'the', 'weather', 'rather'."
  },
  {
    "id": 121,
    "en": "Thoroughly think through the theory.",
    "ipa_rp": "/ˈθʌrəli θɪŋk θruː ðə ˈθɪəri/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "hard",
    "notes": "Five /θ/ sounds! Very challenging tongue workout."
  },
  {
    "id": 122,
    "en": "The southern weather is rather warm.",
    "ipa_rp": "/ðə ˈsʌðən ˈweðə ɪz ˈrɑːðə wɔːm/",
    "target_phonemes": ["ð"],
    "difficulty": "easy",
    "notes": "Focus on /ð/ throughout. No /θ/ in this phrase."
  },
  {
    "id": 123,
    "en": "Think of something else.",
    "ipa_rp": "/θɪŋk əv ˈsʌmθɪŋ els/",
    "target_phonemes": ["θ"],
    "difficulty": "easy",
    "notes": "/θ/ in 'think' and 'something'. Good starter phrase."
  },
  {
    "id": 124,
    "en": "That's the thing about the north.",
    "ipa_rp": "/ðæts ðə θɪŋ əˈbaʊt ðə nɔːθ/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/ð/ in 'that's', 'the' (twice). /θ/ in 'thing', 'north'."
  },
  {
    "id": 125,
    "en": "The author thinks this is worthwhile.",
    "ipa_rp": "/ði ˈɔːθə θɪŋks ðɪs ɪz ˈwɜːθwaɪl/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/θ/ in 'author', 'thinks', 'worthwhile'. /ð/ in 'the', 'this'."
  },
  {
    "id": 126,
    "en": "There's nothing like a warm bath.",
    "ipa_rp": "/ðeəz ˈnʌθɪŋ laɪk ə wɔːm bɑːθ/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "easy",
    "notes": "/ð/ in 'there's'. /θ/ in 'nothing', 'bath'."
  },
  {
    "id": 127,
    "en": "They thought the therapy was helpful.",
    "ipa_rp": "/ðeɪ θɔːt ðə ˈθerəpi wəz ˈhelpf(ə)l/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "medium",
    "notes": "/ð/ in 'they', 'the'. /θ/ in 'thought', 'therapy'."
  },
  {
    "id": 128,
    "en": "Smooth leather feels rather nice.",
    "ipa_rp": "/smuːð ˈleðə fiːlz ˈrɑːðə naɪs/",
    "target_phonemes": ["ð"],
    "difficulty": "easy",
    "notes": "Focus on final /ð/ in 'smooth', and /ð/ in 'leather', 'rather'."
  },
  {
    "id": 129,
    "en": "The sixth month brings warmth.",
    "ipa_rp": "/ðə sɪksθ mʌnθ brɪŋz wɔːmθ/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "hard",
    "notes": "Challenging clusters: 'sixth' /sɪksθ/, 'month' /mʌnθ/, 'warmth' /wɔːmθ/."
  },
  {
    "id": 130,
    "en": "With faith and truth, we thrive together.",
    "ipa_rp": "/wɪð feɪθ ənd truːθ wi θraɪv təˈɡeðə/",
    "target_phonemes": ["θ", "ð"],
    "difficulty": "hard",
    "notes": "/ð/ in 'with', 'together'. /θ/ in 'faith', 'truth', 'thrive'."
  }
]
```

- [ ] **Step 2: Commit**

```bash
git add data/phrases_level_1.json
git commit -m "feat: add 30 phrases for Level 1 (θ/ð sounds)"
```

---

## Phase 5: Integration

### Task 17: Run All Tests

**Files:** None (testing only)

- [ ] **Step 1: Run all tests**

Run: `cd /Users/georgeorellanasv/accent-trainer && python3 -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Fix any failing tests**

If tests fail, debug and fix the issues.

- [ ] **Step 3: Commit test fixes if any**

```bash
git add -A
git commit -m "fix: resolve test failures"
```

---

### Task 18: Start Server and Manual Test

**Files:** None (manual testing)

- [ ] **Step 1: Initialize database and start server**

```bash
cd /Users/georgeorellanasv/accent-trainer
python3 -c "from database import init_db; init_db(); print('DB initialized')"
python3 server.py
```

Expected: Server starts on http://127.0.0.1:8001

- [ ] **Step 2: Test API endpoints manually**

Open browser to http://127.0.0.1:8001/docs
Test the following endpoints:
- POST /api/user - Create user
- GET /api/levels?user_id={id} - Get journey map
- GET /api/level/1/phrases?user_id={id} - Get level 1 phrases

- [ ] **Step 3: Test TTS endpoint**

```bash
curl "http://127.0.0.1:8001/api/tts/text?text=Hello&voice=female" --output test.wav
# Play test.wav to verify Azure TTS works
```

---

### Task 19: Final Commit and Push

- [ ] **Step 1: Review all changes**

```bash
git status
git log --oneline -10
```

- [ ] **Step 2: Push to remote**

```bash
git push origin master
```

---

## Summary

This plan transforms the MVP into a complete pronunciation training system with:

1. **SQLite persistence** for user profiles and progress
2. **Modular backend** with FastAPI routers
3. **Azure TTS Neural** for consistent RP reference audio
4. **Strict scoring** with RP phoneme weighting
5. **Diagnostic assessment** with phoneme analysis
6. **Journey map** with 6 levels
7. **Waveform visualization** for audio comparison
8. **30+ phrases** for Level 1 (/θ/ and /ð/ sounds)

Remaining work for future tasks:
- Create phrases for Levels 2-6 (30+ each)
- Build diagnostic.html UI
- Build main index.html with journey map
- Add more visual polish and animations
