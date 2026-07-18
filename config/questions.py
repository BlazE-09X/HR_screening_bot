from dataclasses import dataclass


@dataclass
class Question:
    key: str          # уникальный ключ для хранения в БД
    text: str         # текст вопроса кандидату


QUESTIONNAIRE: list[Question] = [
    Question(key="motivation", text="Почему вы хотите работать в нашей компании?"),
    Question(key="experience", text="Расскажите о вашем последнем опыте работы."),
    Question(key="strengths", text="Какие ваши сильные стороны как специалиста?"),
    Question(key="conflict", text="Опишите ситуацию, когда у вас возник конфликт на работе. Как вы его решили?"),
    Question(key="teamwork", text="Предпочитаете работать в команде или самостоятельно? Почему?"),
]