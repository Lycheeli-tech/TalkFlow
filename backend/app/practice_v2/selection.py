from random import Random, SystemRandom

from app.course.catalog_v1 import COURSE_CATALOG_V1, QuestionDefinition

QUESTIONS = tuple(question for course in COURSE_CATALOG_V1 for question in course.questions)
QUESTION_BY_ID = {question.id: question for question in QUESTIONS}


def select_questions(count: int, *, seed: int | None = None) -> tuple[QuestionDefinition, ...]:
    if count not in (3, 5):
        raise ValueError("Practice requires three or five questions.")
    random = SystemRandom() if seed is None else Random(seed)
    return tuple(random.sample(QUESTIONS, count))
