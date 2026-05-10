from pydantic import BaseModel, Field
from typing import Optional, List, Literal
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
    word_scores: List[dict]

class LevelProgress(BaseModel):
    level: int
    completed: bool = False
    avg_score: float = 0.0
    phrases_practiced: int = 0

class DiagnosticResult(BaseModel):
    phoneme_scores: List[PhonemeScore]
    problem_areas: List[str]
    recommended_level: int

class Phrase(BaseModel):
    id: int
    en: str
    ipa_rp: str
    target_phonemes: List[str]
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
    words: List[dict]
    tips: List[dict]
    focus: str
    encouragement: str
