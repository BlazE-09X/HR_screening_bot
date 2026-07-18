import sqlite3
import json
import logging
from contextlib import contextmanager
from typing import Optional

from database.models import Candidate, Answer

logger = logging.getLogger(__name__)


class CandidateRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("Ошибка при работе с БД, изменения отменены")
            raise
        finally:
            conn.close()

    def create_candidate(self, candidate: Candidate) -> int:
        """Создаёт кандидата, возвращает его новый id."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO candidates (telegram_id, full_name, created_at, status)
                   VALUES (?, ?, ?, ?)""",
                (candidate.telegram_id, candidate.full_name,
                 candidate.created_at.isoformat(), candidate.status)
            )
            return cursor.lastrowid

    def get_candidate(self, candidate_id: int) -> Optional[Candidate]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            return Candidate(**dict(row)) if row else None

    def add_answer(self, answer: Answer) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO answers (candidate_id, question_key, answer_text)
                   VALUES (?, ?, ?)""",
                (answer.candidate_id, answer.question_key, answer.answer_text)
            )
            return cursor.lastrowid

    def save_ai_analysis(self, candidate_id: int, analysis_json: str, score: int) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE candidates
                   SET ai_analysis_json = ?, ai_score = ?, status = 'completed'
                   WHERE id = ?""",
                (analysis_json, score, candidate_id)
            )