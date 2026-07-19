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
    
    def get_candidate_with_answers(self, candidate_id: int) -> tuple[Candidate, list[Answer]]:
        """Возвращает кандидата вместе со всеми его ответами."""
        candidate = self.get_candidate(candidate_id)
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM answers WHERE candidate_id = ?", (candidate_id,)
            ).fetchall()
            answers = [Answer(**dict(row)) for row in rows]
        return candidate, answers

    def save_resume_file_id(self, candidate_id: int, file_id: str) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE candidates SET resume_file_id = ? WHERE id = ?",
                (file_id, candidate_id)
            )

    def initialize_schema(self, schema_path: str = "database/migrations/schema.sql") -> None:
        """Создаёт таблицы, если их ещё нет. Безопасно вызывать при каждом запуске."""
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        with self._get_connection() as conn:
            conn.executescript(schema_sql)
        logger.info("Схема базы данных проверена/создана")
    
    def save_answer_scores(self, candidate_id: int, scores: dict[str, int]) -> None:
        """Записывает оценку 1-10 в каждый существующий ответ кандидата."""
        with self._get_connection() as conn:
            for question_key, score in scores.items():
                conn.execute(
                    """UPDATE answers SET answer_score = ?
                       WHERE candidate_id = ? AND question_key = ?""",
                    (score, candidate_id, question_key)
                )
    
    def search_by_name(self, query: str) -> list[Candidate]:
        """Поиск кандидатов по части имени (регистронезависимый)."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM candidates WHERE full_name LIKE ? AND status = 'completed'",
                (f"%{query}%",)
            ).fetchall()
            return [Candidate(**dict(row)) for row in rows]

    def search_by_min_score(self, min_score: int) -> list[Candidate]:
        """Кандидаты с AI Score не ниже указанного, отсортированы по убыванию."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM candidates
                   WHERE ai_score >= ? AND status = 'completed'
                   ORDER BY ai_score DESC""",
                (min_score,)
            ).fetchall()
            return [Candidate(**dict(row)) for row in rows]

    def search_by_skill(self, skill: str) -> list[Candidate]:
        """Поиск по навыку — ищет вхождение слова в JSON-анализе (key_skills)."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM candidates
                   WHERE ai_analysis_json LIKE ? AND status = 'completed'""",
                (f"%{skill}%",)
            ).fetchall()
            return [Candidate(**dict(row)) for row in rows]

    def get_candidates_with_red_flags(self) -> list[Candidate]:
        """Кандидаты, у которых risks не пустой в AI-анализе."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM candidates
                   WHERE status = 'completed' AND ai_analysis_json LIKE '%"risks":[%'
                   AND ai_analysis_json NOT LIKE '%"risks":[]%'"""
            ).fetchall()
            return [Candidate(**dict(row)) for row in rows]

    def get_all_completed(self) -> list[Candidate]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM candidates WHERE status = 'completed' ORDER BY created_at DESC"
            ).fetchall()
            return [Candidate(**dict(row)) for row in rows]
    
    def get_candidates_by_ids(self, ids: list[int]) -> list[Candidate]:
        placeholders = ",".join("?" * len(ids))
        with self._get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM candidates WHERE id IN ({placeholders})", ids
            ).fetchall()
            return [Candidate(**dict(row)) for row in rows]