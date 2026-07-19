import logging
from google import genai
from google.genai import types

from ai.schemas import CandidateAnalysis

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self, api_key: str, model: str = None):
        self.client = genai.Client(api_key=api_key)
        self.model = model or "gemini-flash-latest"

    def analyze_candidate(self, prompt: str) -> CandidateAnalysis:
        """Отправляет промпт и возвращает строго типизированный результат."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CandidateAnalysis,
                ),
            )
            return CandidateAnalysis.model_validate_json(response.text)
        except Exception:
            logger.exception("Ошибка при обращении к Gemini API")
            raise