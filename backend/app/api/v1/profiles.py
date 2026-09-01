from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.ai.interfaces import ProfileExtractor
from app.api.dependencies import (
    get_current_user,
    get_profile_extractor,
    get_profile_repository,
)
from app.core.config import get_settings
from app.repositories.profiles import ProfileRepository
from app.schemas import (
    AuthenticatedUser,
    CandidateExtractionResponse,
    ConfirmedProfile,
    ProfileConfirmationRequest,
    TextProfileImport,
)
from app.services.documents import PdfResumeParser, ResumeValidationError
from app.services.profiles import ProfileService

router = APIRouter()


def profile_service(
    repository: ProfileRepository = Depends(get_profile_repository),
    extractor: ProfileExtractor = Depends(get_profile_extractor),
) -> ProfileService:
    return ProfileService(repository, extractor)


@router.post("/sources/text", response_model=CandidateExtractionResponse, status_code=201)
async def import_background_text(
    payload: TextProfileImport,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: ProfileService = Depends(profile_service),
) -> CandidateExtractionResponse:
    source, candidate = await service.create_text_candidate(
        user_id=current_user.id,
        target_role=payload.target_role,
        raw_text=payload.raw_text,
    )
    return CandidateExtractionResponse(
        source_id=source.id,
        extractor_version=source.extractor_version or "unknown",
        candidate=candidate,
    )


@router.post("/sources/pdf", response_model=CandidateExtractionResponse, status_code=201)
async def import_resume_pdf(
    target_role: Annotated[str, Form(min_length=1, max_length=160)],
    resume: Annotated[UploadFile, File()],
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: ProfileService = Depends(profile_service),
) -> CandidateExtractionResponse:
    settings = get_settings()
    content = await resume.read(settings.max_resume_bytes + 1)
    try:
        raw_text = PdfResumeParser(settings.max_resume_bytes).parse(
            content=content,
            content_type=resume.content_type,
            filename=resume.filename,
        )
    except ResumeValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    source, candidate = await service.create_pdf_candidate(
        user_id=current_user.id,
        target_role=target_role,
        filename=resume.filename or "resume.pdf",
        raw_text=raw_text,
    )
    return CandidateExtractionResponse(
        source_id=source.id,
        extractor_version=source.extractor_version or "unknown",
        candidate=candidate,
    )


@router.post("/confirm", response_model=ConfirmedProfile)
async def confirm_profile(
    payload: ProfileConfirmationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: ProfileService = Depends(profile_service),
) -> ConfirmedProfile:
    try:
        return await service.confirm_candidate(
            user_id=current_user.id,
            source_id=payload.source_id,
            edited_candidate=payload.candidate,
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/me", response_model=ConfirmedProfile)
async def get_confirmed_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: ProfileService = Depends(profile_service),
) -> ConfirmedProfile:
    profile = await service.get_confirmed(current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No confirmed profile exists."
        )
    return profile
