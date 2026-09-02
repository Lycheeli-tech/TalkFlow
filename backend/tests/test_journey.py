from app.schemas import UserState
from app.services.journey import JourneyService


def test_journey_projects_fixed_phases_and_current_day() -> None:
    result = JourneyService().build(
        UserState(
            id="11111111-1111-4111-8111-111111111111", current_day=11, current_phase="TRANSFER"
        )
    )

    assert len(result.days) == 30
    assert result.days[0].phase == "BUILD"
    assert result.days[9].status == "COMPLETED"
    assert result.days[10].status == "CURRENT"
    assert result.days[20].phase == "PERFORM"
