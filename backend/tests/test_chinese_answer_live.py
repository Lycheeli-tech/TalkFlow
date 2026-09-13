import os

import pytest

from app.core.config import get_settings
from app.course.chinese_organizer import (
    BailianChineseAnswerOrganizer,
    OrganizedDraft,
    OrganizedSegment,
    validate_organized_draft,
)


@pytest.mark.skipif(os.getenv("RUN_COURSE_AI_LIVE") != "1", reason="opt-in Bailian text regression")
@pytest.mark.asyncio
async def test_live_chinese_translation_preserves_role_negation_and_rejects_fabrication():
    settings = get_settings()
    provider = BailianChineseAnswerOrganizer(
        api_key=settings.bailian_api_key,
        base_url=settings.bailian_compatible_base_url,
        model=settings.bailian_text_model,
    )
    transcript = "这是合成测试。我只协助测试，没有负责整个项目。我不知道最终收入数据。"
    draft = await provider.organize(transcript)
    english = validate_organized_draft(transcript, draft)
    assert english and await provider.verify(transcript, draft)
    fabricated = OrganizedDraft(
        segments=[
            OrganizedSegment(
                source_excerpt=transcript,
                english="I led the entire project and increased revenue by 50%.",
            )
        ]
    )
    assert not await provider.verify(transcript, fabricated)
