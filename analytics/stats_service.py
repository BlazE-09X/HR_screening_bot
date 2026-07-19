import json
import logging
from collections import Counter
from dataclasses import dataclass

from database.repository import CandidateRepository

logger = logging.getLogger(__name__)


@dataclass
class StatsSnapshot:
    total_candidates: int
    completed_candidates: int
    average_score: float
    recommended_count: int
    red_flag_count: int
    top_skills: list[tuple[str, int]]


class StatsService:
    def __init__(self, repo: CandidateRepository):
        self.repo = repo

    def build_snapshot(self) -> StatsSnapshot:
        candidates = self.repo.get_all_completed()

        if not candidates:
            return StatsSnapshot(
                total_candidates=0, completed_candidates=0, average_score=0.0,
                recommended_count=0, red_flag_count=0, top_skills=[],
            )

        skill_counter: Counter[str] = Counter()
        scores: list[int] = []
        recommended_count = 0
        red_flag_count = 0

        for candidate in candidates:
            if not candidate.ai_analysis_json:
                continue
            analysis = json.loads(candidate.ai_analysis_json)

            if candidate.ai_score is not None:
                scores.append(candidate.ai_score)

            skill_counter.update(analysis.get("key_skills", []))

            if analysis.get("risks"):
                red_flag_count += 1

            # Считаем "рекомендованным" кандидата с высоким score и совпадением
            if candidate.ai_score and candidate.ai_score >= 7:
                recommended_count += 1

        average_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        return StatsSnapshot(
            total_candidates=len(candidates),
            completed_candidates=len(candidates),
            average_score=average_score,
            recommended_count=recommended_count,
            red_flag_count=red_flag_count,
            top_skills=skill_counter.most_common(10),
        )