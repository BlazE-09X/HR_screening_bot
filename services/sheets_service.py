import logging

import gspread

from database.models import Candidate, Answer

logger = logging.getLogger(__name__)

SHEET_HEADERS = [
    "ID", "Telegram ID", "Имя", "Дата прохождения", "Статус",
    "AI Score", "Match %", "Резюме", "Краткий анализ", "Красные флаги",
]


class SheetsService:
    """Отвечает за синхронизацию кандидатов с Google Sheets ('зеркало' для рекрутера)."""

    def __init__(self, credentials_path: str, sheet_id: str):
        self.client = gspread.service_account(filename=credentials_path)
        self.sheet = self.client.open_by_key(sheet_id).sheet1
        self._ensure_headers()

    def _ensure_headers(self) -> None:
        """Проверяет, что в таблице есть заголовки, и добавляет их, если нет."""
        first_row = self.sheet.row_values(1)
        if first_row != SHEET_HEADERS:
            self.sheet.insert_row(SHEET_HEADERS, index=1)
            logger.info("Заголовки добавлены в Google Sheets")

    def append_candidate(self, candidate: Candidate, analysis: dict | None) -> None:
        """Добавляет строку с кандидатом. Вызывается после завершения AI-анализа."""
        try:
            row = [
                candidate.id,
                candidate.telegram_id,
                candidate.full_name,
                candidate.created_at.strftime("%Y-%m-%d %H:%M"),
                candidate.status,
                analysis.get("overall_score") if analysis else "",
                analysis.get("match_percentage") if analysis else "",
                "Есть" if candidate.resume_file_id else "Нет",
                analysis.get("summary") if analysis else "",
                ", ".join(analysis.get("risks", [])) if analysis else "",
            ]
            self.sheet.append_row(row)
            logger.info(f"Кандидат {candidate.id} добавлен в Google Sheets")
        except Exception:
            # Sheets — это "зеркало", а не основной источник данных.
            # Если запись сюда не удалась — кандидат всё равно уже в SQLite, ничего не потеряно.
            logger.exception(f"Не удалось записать кандидата {candidate.id} в Google Sheets")