ENGLISH_ANSWER_ENABLED_COURSE_IDS = frozenset({"course-11"})


def english_answer_is_enabled(course_id: str) -> bool:
    return course_id in ENGLISH_ANSWER_ENABLED_COURSE_IDS
