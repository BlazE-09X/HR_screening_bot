import json
import logging
from dataclasses import dataclass

from database.repository import CandidateRepository
from database.models import Candidate

logger = logging.getLogger(__name__)


@dataclass
class CandidateSearchResult:
    candidate: Candidate
    summary: str
    overall_score: int
    match_percentage: int


class SearchService:
    def __init__(self, repo: CandidateRepository):
        self.repo = repo

    def search(self, query: str) -> list[CandidateSearchResult]:
        """Универсальный поиск: пробует по имени, затем по навыку."""
        candidates = self.repo.search_by_name(query)
        if not candidates:
            candidates = self.repo.search_by_skill(query)
        return [self._to_result(c) for c in candidates]

    def top_by_score(self, min_score: int = 7) -> list[CandidateSearchResult]:
        candidates = self.repo.search_by_min_score(min_score)
        return [self._to_result(c) for c in candidates]

    def with_red_flags(self) -> list[CandidateSearchResult]:
        candidates = self.repo.get_candidates_with_red_flags()
        return [self._to_result(c) for c in candidates]

    @staticmethod
    def _to_result(candidate: Candidate) -> CandidateSearchResult:
        analysis = json.loads(candidate.ai_analysis_json) if candidate.ai_analysis_json else {}
        return CandidateSearchResult(
            candidate=candidate,
            summary=analysis.get("summary", ""),
            overall_score=candidate.ai_score or 0,
            match_percentage=analysis.get("match_percentage", 0),
        )