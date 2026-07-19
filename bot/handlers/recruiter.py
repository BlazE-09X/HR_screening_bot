import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.filters import IsRecruiter
from services.search_service import SearchService, CandidateSearchResult
from services.sheets_service import SheetsService
from ai.recruiter_analyzer import RecruiterQueryService
from analytics.stats_service import StatsService

logger = logging.getLogger(__name__)
router = Router()


class ResetStates(StatesGroup):
    waiting_for_confirmation = State()


def register_recruiter_handlers(
    search_service: SearchService,
    recruiter_query_service: RecruiterQueryService,
    stats_service: StatsService,
    sheets_service_ref: SheetsService,
    recruiter_ids: list[int],
) -> Router:
    router.message.filter(IsRecruiter(recruiter_ids))

    @router.message(Command("search"))
    async def search_candidates(message: Message, command: CommandObject):
        if not command.args:
            await message.answer("Использование: /search <имя или навык>\nНапример: /search лидерство")
            return
        results = search_service.search(command.args.strip())
        await message.answer(_format_results(results, title=f"Поиск: «{command.args}»"))

    @router.message(Command("top"))
    async def top_candidates(message: Message, command: CommandObject):
        min_score = int(command.args) if command.args and command.args.isdigit() else 7
        results = search_service.top_by_score(min_score)
        await message.answer(_format_results(results, title=f"Кандидаты со Score ≥ {min_score}"))

    @router.message(Command("redflags"))
    async def red_flag_candidates(message: Message):
        results = search_service.with_red_flags()
        await message.answer(_format_results(results, title="Кандидаты с красными флагами"))

    @router.message(Command("ask"))
    async def ask_ai(message: Message, command: CommandObject):
        if not command.args:
            await message.answer(
                "Использование: /ask <вопрос>\n"
                "Например: /ask Кого из кандидатов 1, 3 и 5 лучше пригласить на менеджера по продажам?"
            )
            return
        await message.answer("Анализирую... 🤔")
        all_candidates = search_service.repo.get_all_completed()
        candidates_data = [
            {"id": c.id, "full_name": c.full_name, "analysis_json": c.ai_analysis_json}
            for c in all_candidates
        ]
        answer = recruiter_query_service.ask(command.args, candidates_data)
        await message.answer(answer)

    @router.message(Command("stats"))
    async def show_stats(message: Message):
        snapshot = stats_service.build_snapshot()
        if snapshot.total_candidates == 0:
            await message.answer("Пока нет ни одного завершённого кандидата.")
            return
        skills_text = "\n".join(
            f"   {i+1}. {skill} — {count}"
            for i, (skill, count) in enumerate(snapshot.top_skills)
        ) or "   нет данных"
        text = (
            f"📊 Статистика\n\n"
            f"Всего кандидатов: {snapshot.total_candidates}\n"
            f"Средний AI Score: {snapshot.average_score}/10\n"
            f"Рекомендовано (score ≥ 7): {snapshot.recommended_count}\n"
            f"С красными флагами: {snapshot.red_flag_count}\n\n"
            f"Топ навыков:\n{skills_text}"
        )
        await message.answer(text)

    @router.message(Command("reset"))
    async def reset_data_request(message: Message, state: FSMContext):
        await message.answer(
            "Вы собираетесь безвозвратно удалить все данные кандидатов "
            "из базы данных и Google Таблицы.\n\n"
            "Для подтверждения отправьте: ПОДТВЕРДИТЬ\n"
            "Для отмены — любое другое сообщение."
        )
        await state.set_state(ResetStates.waiting_for_confirmation)

    @router.message(ResetStates.waiting_for_confirmation)
    async def reset_data_confirm(message: Message, state: FSMContext):
        await state.clear()
        if message.text.strip() != "ПОДТВЕРДИТЬ":
            await message.answer("Действие отменено. Данные не были изменены.")
            return
        try:
            search_service.repo.clear_all_data()
            sheets_service_ref.clear_all()
            await message.answer("Данные успешно удалены. База данных и таблица очищены.")
        except Exception:
            logger.exception("Ошибка при очистке данных")
            await message.answer(
                "Произошла ошибка при удалении данных. "
                "Часть данных могла быть удалена не полностью. Проверьте базу данных вручную."
            )

    @router.message(Command("help"))
    async def show_help(message: Message):
        text = (
            "Доступные команды для рекрутера:\n\n"
            "/search <запрос> — поиск кандидатов по имени или навыку. "
            "Пример: /search лидерство\n\n"
            "/top <балл> — список кандидатов с AI Score не ниже указанного значения. "
            "По умолчанию используется порог 7. Пример: /top 8\n\n"
            "/redflags — вывод кандидатов, по которым система выявила потенциальные риски.\n\n"
            "/stats — сводная статистика по всем кандидатам: средний балл, "
            "количество рекомендованных, распределение навыков.\n\n"
            "/ask <вопрос> — свободный запрос к ИИ-ассистенту с опорой на данные анкет. "
            "Пример: /ask Кого из кандидатов лучше пригласить на позицию менеджера?\n\n"
            "/reset — полное удаление всех данных кандидатов из базы данных и Google Таблицы. "
            "Требует дополнительного подтверждения.\n\n"
            "/help — вывод данного списка команд."
        )
        await message.answer(text)

    return router


def _format_results(results: list[CandidateSearchResult], title: str) -> str:
    if not results:
        return f"{title}\n\nНичего не найдено."
    lines = [f"{title}\n"]
    for r in results:
        lines.append(
            f"👤 #{r.candidate.id} {r.candidate.full_name}\n"
            f"   Score: {r.overall_score}/10 | Match: {r.match_percentage}%\n"
            f"   {r.summary}\n"
        )
    return "\n".join(lines)