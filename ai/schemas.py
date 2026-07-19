from pydantic import BaseModel, Field
from typing import List

class AnswerScore(BaseModel):
    question_key: str = Field(description="Ключ вопроса, как в анкете")
    score: int = Field(description="Оценка ответа от 1 до 10", ge=1, le=10)


class CandidateAnalysis(BaseModel):
    summary: str = Field(description="Краткое резюме по кандидату, 2-3 предложения")
    key_skills: List[str] = Field(description="Ключевые навыки, выявленные из ответов")
    strengths: List[str] = Field(description="Сильные стороны кандидата")
    weaknesses: List[str] = Field(description="Слабые стороны кандидата")
    risks: List[str] = Field(description="Потенциальные риски (красные флаги), если есть")
    match_percentage: int = Field(description="Оценка соответствия вакансии, 0-100", ge=0, le=100)
    recommendation: str = Field(description="Рекомендация рекрутеру: приглашать/не приглашать и почему")
    interview_questions: List[str] = Field(description="Вопросы для очного собеседования")
    overall_score: int = Field(description="Общий рейтинг кандидата 1-10", ge=1, le=10)
    answer_scores: List[AnswerScore] = Field(description="Оценка каждого ответа по отдельности")