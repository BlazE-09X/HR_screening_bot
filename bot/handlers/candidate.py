import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from bot.states import QuestionnaireStates
from config.questions import QUESTIONNAIRE
from database.models import Candidate, Answer
from database.repository import CandidateRepository
from services.candidate_service import CandidateService

logger = logging.getLogger(__name__)
router = Router()


def register_candidate_handlers(repo: CandidateRepository, candidate_service: CandidateService) -> Router:
    """Регистрирует обработчики, передавая им repository через замыкание."""

    @router.message(CommandStart())
    async def start_questionnaire(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            "Здравствуйте! Я помогу вам пройти первичный отбор.\n"
            "Как вас зовут? (Имя и фамилия)"
        )
        await state.set_state(QuestionnaireStates.waiting_for_name)

    @router.message(QuestionnaireStates.waiting_for_name)
    async def process_name(message: Message, state: FSMContext):
        full_name = message.text.strip()

        candidate = Candidate(telegram_id=message.from_user.id, full_name=full_name)
        candidate_id = repo.create_candidate(candidate)

        # Сохраняем в FSM: id кандидата и номер текущего вопроса
        await state.update_data(candidate_id=candidate_id, question_index=0)

        first_question = QUESTIONNAIRE[0]
        await message.answer(f"Приятно познакомиться, {full_name}!\n\n{first_question.text}")
        await state.set_state(QuestionnaireStates.answering_questions)

    @router.message(QuestionnaireStates.answering_questions)
    async def process_answer(message: Message, state: FSMContext):
        data = await state.get_data()
        candidate_id = data["candidate_id"]
        question_index = data["question_index"]

        current_question = QUESTIONNAIRE[question_index]
        answer = Answer(
            candidate_id=candidate_id,
            question_key=current_question.key,
            answer_text=message.text.strip(),
        )
        repo.add_answer(answer)

        next_index = question_index + 1

        if next_index < len(QUESTIONNAIRE):
            # Есть ещё вопросы — задаём следующий
            await state.update_data(question_index=next_index)
            await message.answer(QUESTIONNAIRE[next_index].text)
        else:
            # Вопросы закончились — просим резюме
            await message.answer(
                "Спасибо за ответы! Пришлите, пожалуйста, ваше резюме в формате PDF.\n"
                "Если резюме нет — напишите «пропустить»."
            )
            await state.set_state(QuestionnaireStates.waiting_for_resume)
    

    @router.message(QuestionnaireStates.waiting_for_resume, F.document)
    async def process_resume(message: Message, state: FSMContext):
        if message.document.mime_type != "application/pdf":
            await message.answer("Пожалуйста, отправьте файл именно в формате PDF.")
            return

        data = await state.get_data()
        candidate_id = data["candidate_id"]

        # Сохраняем file_id — сам файл продолжает храниться на серверах Telegram,
        # мы просто запоминаем "ссылку" на него
        repo.save_resume_file_id(candidate_id, message.document.file_id)

        await finish_questionnaire(message, state, candidate_id)

    @router.message(QuestionnaireStates.waiting_for_resume, F.text)
    async def skip_resume(message: Message, state: FSMContext):
        data = await state.get_data()
        candidate_id = data["candidate_id"]

        if message.text.strip().lower() != "пропустить":
            await message.answer(
                "Если хотите прикрепить резюме — пришлите PDF-файл. "
                "Если резюме нет, напишите «пропустить»."
            )
            return

        await finish_questionnaire(message, state, candidate_id)

    async def finish_questionnaire(message: Message, state: FSMContext, candidate_id: int):
        await message.answer(
            "Спасибо, что прошли анкету! Мы свяжемся с вами после рассмотрения. Удачи!"
        )
        await state.clear()
        logger.info(f"Кандидат {candidate_id} завершил анкету, запускается анализ")

        candidate_service.process_completed_candidate(candidate_id)
    return router