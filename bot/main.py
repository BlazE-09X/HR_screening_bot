import asyncio
import logging

from aiogram import Bot, Dispatcher

from config.settings import settings
from database.repository import CandidateRepository
from ai.client import GeminiClient
from ai.recruiter_analyzer import RecruiterQueryService
from services.candidate_service import CandidateService
from services.sheets_service import SheetsService
from services.search_service import SearchService
from analytics.stats_service import StatsService
from bot.handlers.candidate import register_candidate_handlers
from bot.handlers.recruiter import register_recruiter_handlers


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    # 1. Инициализируем базу данных
    repo = CandidateRepository(db_path=settings.database_path)
    repo.initialize_schema()

    # 2. Инициализируем AI-клиент
    ai_client = GeminiClient(api_key=settings.gemini_api_key)

    # 3. Инициализируем Google Sheets
    sheets_service = SheetsService(
        credentials_path=settings.google_sheets_credentials_path,
        sheet_id=settings.google_sheet_id,
    )

    # 4. Собираем сервисы
    candidate_service = CandidateService(repo=repo, ai_client=ai_client, sheets_service=sheets_service)
    search_service = SearchService(repo=repo)
    recruiter_query_service = RecruiterQueryService(ai_client=ai_client)
    stats_service = StatsService(repo=repo)

    # 5. Инициализируем бота и диспетчер aiogram
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # 6. Регистрируем обработчики
    dp.include_router(register_candidate_handlers(repo, candidate_service))
    dp.include_router(register_recruiter_handlers(
        search_service, recruiter_query_service, stats_service, sheets_service, settings.recruiter_ids
    ))

    logger.info("Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())