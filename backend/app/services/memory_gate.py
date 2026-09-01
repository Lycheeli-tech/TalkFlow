from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.schemas import ErrorPattern, ErrorPatternRules, Story


class MemoryGate:
    """The only service allowed to promote proposals into durable memory records."""

    def propose_error(
        self, *, user_id: UUID, pattern_type: str, original_example: str
    ) -> ErrorPattern:
        now = datetime.now(UTC)
        return ErrorPattern(
            id=uuid4(),
            user_id=user_id,
            pattern_type=pattern_type,
            original_example=original_example,
            first_seen=now,
            last_seen=now,
        )

    def record_error_evidence(
        self, pattern: ErrorPattern, *, repeated: bool, corrected: bool = False
    ) -> ErrorPattern:
        occurrence_count = pattern.occurrence_count + (1 if repeated else 0)
        corrections = pattern.successful_correction_count + (1 if corrected else 0)
        if (
            pattern.status == "CANDIDATE"
            and occurrence_count >= self.rules.active_occurrences_required
        ):
            status = "ACTIVE"
        elif corrected and pattern.status == "ACTIVE":
            status = "IMPROVING"
        elif (
            corrected
            and pattern.status == "IMPROVING"
            and corrections >= self.rules.resolved_corrections_required
        ):
            status = "RESOLVED"
        else:
            status = pattern.status
        return pattern.model_copy(
            update={
                "occurrence_count": occurrence_count,
                "successful_correction_count": corrections,
                "status": status,
                "last_seen": datetime.now(UTC),
            }
        )

    def confirm_story(
        self,
        *,
        user_id: UUID,
        title: str,
        content: str,
        confirmed_by_user: bool,
        source_type: str = "USER",
        source_document_id: UUID | None = None,
        source_attempt_id: UUID | None = None,
    ) -> Story:
        if not confirmed_by_user:
            raise PermissionError("A story must be confirmed by the user before persistence.")
        now = datetime.now(UTC)
        return Story(
            id=uuid4(),
            user_id=user_id,
            title=title,
            content=content,
            source_type=source_type,
            source_document_id=source_document_id,
            source_attempt_id=source_attempt_id,
            confirmed_by_user=True,
            created_at=now,
            updated_at=now,
        )

    def __init__(self, rules: ErrorPatternRules | None = None) -> None:
        self.rules = rules or ErrorPatternRules()
