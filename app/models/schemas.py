from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Question Models ────────────────────────────────────────────────────────

class QuestionBase(BaseModel):
    text: str
    options: List[str]                  # ["A) ...", "B) ...", ...]
    correct_answer: str                 # "A", "B", "C", or "D"
    difficulty: float = Field(..., ge=0.1, le=1.0)
    topic: str                          # e.g. "Algebra", "Vocabulary"
    tags: List[str] = []


class QuestionInDB(QuestionBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class QuestionResponse(BaseModel):
    """Sent to client — no correct_answer exposed."""
    id: str
    text: str
    options: List[str]
    difficulty: float
    topic: str
    tags: List[str]


# ─── Session Models ──────────────────────────────────────────────────────────

class ResponseRecord(BaseModel):
    question_id: str
    topic: str
    difficulty: float
    is_correct: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserSession(BaseModel):
    session_id: str
    student_name: Optional[str] = "Anonymous"
    ability_score: float = 0.5          # θ (theta) in Rasch model, scaled 0–1
    questions_answered: int = 0
    max_questions: int = 10
    is_complete: bool = False
    responses: List[ResponseRecord] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str                         # "A", "B", "C", or "D"


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    updated_ability_score: float
    questions_answered: int
    is_complete: bool
    next_question: Optional[QuestionResponse] = None
    message: str
