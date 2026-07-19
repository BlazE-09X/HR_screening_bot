from ai.client import GeminiClient
from ai.prompts import build_analysis_prompt
from config.settings import settings

qa_pairs = [
    ("motivation", "Почему вы хотите работать в нашей компании?",
     "Мне интересна сфера IT, и я хочу развиваться именно в вашей команде."),
    ("experience", "Расскажите о вашем последнем опыте работы.",
     "Работал стажёром в отделе поддержки клиентов, отвечал на запросы и решал конфликтные ситуации."),
    ("strengths", "Какие ваши сильные стороны как специалиста?",
     "Ответственность, быстро учусь новому, легко нахожу общий язык с людьми."),
    ("conflict", "Опишите ситуацию, когда у вас возник конфликт на работе. Как вы его решили?",
     "Был спор с коллегой из-за распределения задач, обсудили спокойно и договорились."),
    ("teamwork", "Предпочитаете работать в команде или самостоятельно? Почему?",
     "Предпочитаю команду, вместе быстрее находим решения."),
]

prompt = build_analysis_prompt(full_name="Тестовый Кандидат", qa_pairs=qa_pairs)

client = GeminiClient(api_key=settings.gemini_api_key)
result = client.analyze_candidate(prompt)

print("=== Результат анализа ===")
print(result.model_dump_json(indent=2))