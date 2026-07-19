import json
import logging

from database.repository import CandidateRepository
from database.models import Answer
from ai.client import GeminiClient
from ai.prompts import build_analysis_prompt
from config.questions import QUESTIONNAIRE
from services.sheets_service import SheetsService

logger = logging.getLogger(__name__)

class CandidateService:
    def __init__(self, repo: CandidateRepository, ai_client: GeminiClient, sheets_service: SheetsService):
        self.repo = repo
        self.ai_client = ai_client
        self.sheets_service = sheets_service

    def process_completed_candidate(self, candidate_id: int) -> None:
        candidate, answers = self.repo.get_candidate_with_answers(candidate_id)
        qa_pairs = self._build_qa_pairs(answers)
        prompt = build_analysis_prompt(full_name=candidate.full_name, qa_pairs=qa_pairs)

        analysis_dict = None
        try:
            analysis = self.ai_client.analyze_candidate(prompt)
            analysis_dict = analysis.model_dump()
            self.repo.save_ai_analysis(
                candidate_id=candidate_id,
                analysis_json=analysis.model_dump_json(),
                score=analysis.overall_score,
            )
            scores_dict = {item.question_key: item.score for item in analysis.answer_scores}
            self.repo.save_answer_scores(candidate_id, scores_dict)
            logger.info(f"Кандидат {candidate_id} проанализирован, score={analysis.overall_score}")
        except Exception:
            logger.exception(f"Не удалось проанализировать кандидата {candidate_id}")

        # Отправляем в Sheets в любом случае — даже если AI-анализ не удался,
        # рекрутер должен увидеть, что кандидат прошёл анкету
        updated_candidate, _ = self.repo.get_candidate_with_answers(candidate_id)
        self.sheets_service.append_candidate(updated_candidate, analysis_dict)

    @staticmethod
    def _build_qa_pairs(answers: list[Answer]) -> list[tuple[str, str, str]]:
        """Возвращает (question_key, текст_вопроса, ответ_кандидата) для промпта."""
        question_text_by_key = {q.key: q.text for q in QUESTIONNAIRE}
        answers_by_key = {a.question_key: a.answer_text for a in answers}

        return [
            (key, question_text_by_key[key], answers_by_key.get(key, ""))
            for key in question_text_by_key
        ]