from aiogram.fsm.state import State, StatesGroup


class QuestionnaireStates(StatesGroup):
    waiting_for_name = State()
    answering_questions = State()
    waiting_for_resume = State()