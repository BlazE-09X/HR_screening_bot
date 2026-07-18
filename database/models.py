from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Candidate(BaseModel):
    """Модель кандидата — то, как данные выглядят в коде Python."""
    id: Optional[int] = None
    telegram_id: int
    full_name: str
    resume_file_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "in_progress"
    ai_score: Optional[int] = None
    ai_analysis_json: Optional[str] = None


class Answer(BaseModel):
    """Модель одного ответа кандидата на один вопрос анкеты."""
    id: Optional[int] = None
    candidate_id: int
    question_key: str
    answer_text: str
    answer_score: Optional[int] = None