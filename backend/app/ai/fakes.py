from typing import Any

from app.schemas import (
    AttemptAnalysis,
    CalibrationQuestion,
    CandidateProfile,
    ConfirmedProfile,
)


class FakeLLMService:
    def __init__(self, response: dict[str, Any] | None = None) -> None:
        self._response = response or {"provider": "fake", "status": "ok"}

    async def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            **self._response,
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "input_data": input_data,
        }


class FakeSpeechToTextService:
    provider_name = "fake"

    def __init__(self, transcript: str = "Fixture transcript") -> None:
        self._transcript = transcript

    async def transcribe(self, *, audio: bytes, content_type: str) -> str:
        del audio, content_type
        return self._transcript


class FakeTextToSpeechService:
    async def synthesize(self, *, text: str, voice: str) -> bytes:
        return f"fake-audio:{voice}:{text}".encode()


class FakeCalibrationQuestionGenerator:
    version = "calibration_questions_fixture_v1"

    async def generate(self, *, profile: ConfirmedProfile) -> list[CalibrationQuestion]:
        experience = profile.work_experience[0] if profile.work_experience else profile.target_role
        motivation = profile.career_transition or profile.target_role
        project = (
            profile.projects[0]
            if profile.projects
            else profile.skills[0]
            if profile.skills
            else profile.target_role
        )
        return [
            CalibrationQuestion(
                category="EXPERIENCE", text=f"Tell me about your experience with {experience}."
            ),
            CalibrationQuestion(
                category="MOTIVATION", text=f"Why are you moving toward {motivation}?"
            ),
            CalibrationQuestion(
                category="PROJECT", text=f"Walk me through a project involving {project}."
            ),
        ]


class FakeAnswerAnalyzer:
    version = "answer_analyzer_fixture_v1"

    async def analyze(self, *, question: str, transcript: str) -> AttemptAnalysis:
        del question
        level = "FUNCTIONAL" if len(transcript.split()) >= 5 else "DEVELOPING"
        return AttemptAnalysis(
            fluency=level,
            naturalness=level,
            grammar=level,
            retrieval=level,
            structure=level,
            strengths=["Completed a relevant spoken response."],
            focus_areas=["Use specific examples and clearer transitions."],
            observed_patterns=["Baseline response captured."],
            evidence=[transcript[:160]],
        )


class FakeProfileExtractor:
    version = "profile_extractor_fixture_v1"

    def __init__(self, candidate: CandidateProfile | None = None) -> None:
        self._candidate = candidate

    async def extract(self, *, raw_text: str, target_role: str) -> CandidateProfile:
        if self._candidate is not None:
            return self._candidate.model_copy(update={"target_role": target_role})
        summary = " ".join(raw_text.split())[:240]
        return CandidateProfile(
            target_role=target_role,
            work_experience=[summary] if summary else [],
        )
