import logging
from google.genai import types

from ai.client import GeminiClient

logger = logging.getLogger(__name__)


def build_recruiter_query_prompt(question: str, candidates_data: list[dict]) -> str:
    candidates_text = "\n\n".join(
        f"Кандидат #{c['id']} {c['full_name']}:\n{c['analysis_json']}"
        for c in candidates_data
    )
    return f"""Ты — ассистент рекрутера. Ответь на вопрос рекрутера, опираясь ТОЛЬКО на данные анкет ниже.
Не придумывай факты, которых нет в данных. Если данных недостаточно для ответа — прямо скажи об этом.

Данные кандидатов:
{candidates_text}

Вопрос рекрутера: {question}

Дай аргументированный ответ, ссылаясь на конкретные ID кандидатов и факты из их анкет."""


class RecruiterQueryService:
    def __init__(self, ai_client: GeminiClient):
        self.ai_client = ai_client

    def ask(self, question: str, candidates_data: list[dict]) -> str:
        prompt = build_recruiter_query_prompt(question, candidates_data)
        try:
            response = self.ai_client.client.models.generate_content(
                model=self.ai_client.model,
                contents=prompt,
            )
            return response.text
        except Exception:
            logger.exception("Ошибка при обработке запроса рекрутера")
            return "Не удалось получить ответ от ИИ. Попробуйте ещё раз позже."