from app.schemas import JourneyDay, JourneyResponse, UserState


def phase_for_day(day: int) -> str:
    if day <= 10:
        return "BUILD"
    if day <= 20:
        return "TRANSFER"
    return "PERFORM"


class JourneyService:
    def build(self, state: UserState) -> JourneyResponse:
        return JourneyResponse(
            current_day=state.current_day,
            current_phase=state.current_phase,
            days=[
                JourneyDay(
                    day=day,
                    phase=phase_for_day(day),
                    status=(
                        "COMPLETED"
                        if day < state.current_day
                        or (day == 30 and state.program_completed_at is not None)
                        else "CURRENT"
                        if day == state.current_day
                        else "UPCOMING"
                    ),
                )
                for day in range(1, 31)
            ],
        )
