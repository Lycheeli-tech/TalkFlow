from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.about_me.schemas import (
    AboutMePatch,
    AboutMeView,
    DeleteResult,
    MemoryView,
    ResumeView,
    TargetRoleCreate,
    TargetRoleView,
)
from app.about_me.service import AboutMeService
from app.api.about_me_dependencies import get_about_me_service
from app.api.core_dependencies import get_course_current_user
from app.core.auth import AuthenticatedUser
from app.core.config import get_settings
from app.services.documents import ResumeValidationError

router = APIRouter()


@router.get("", response_model=AboutMeView)
async def get_about_me(
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: AboutMeService = Depends(get_about_me_service),
) -> AboutMeView:
    return AboutMeView.from_snapshot(await service.get(current_user.id))


@router.patch("", response_model=AboutMeView)
async def patch_about_me(
    request: AboutMePatch,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: AboutMeService = Depends(get_about_me_service),
) -> AboutMeView:
    try:
        return AboutMeView.from_snapshot(
            await service.update_facts(current_user.id, request.supplemental_facts)
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/target-roles", response_model=list[TargetRoleView])
async def list_target_roles(
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: AboutMeService = Depends(get_about_me_service),
) -> list[TargetRoleView]:
    return [
        TargetRoleView.from_role(item) for item in (await service.get(current_user.id)).target_roles
    ]


@router.post("/target-roles", response_model=TargetRoleView, status_code=201)
async def create_target_role(
    request: TargetRoleCreate,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: AboutMeService = Depends(get_about_me_service),
) -> TargetRoleView:
    try:
        return TargetRoleView.from_role(
            await service.add_target_role(current_user.id, request.role_name)
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.delete("/target-roles/{role_id}", response_model=DeleteResult)
async def delete_target_role(
    role_id: UUID,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: AboutMeService = Depends(get_about_me_service),
) -> DeleteResult:
    await _delete(lambda: service.delete_target_role(current_user.id, role_id))
    return DeleteResult(deleted_id=role_id)


@router.get("/resumes", response_model=list[ResumeView])
async def list_resumes(
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: AboutMeService = Depends(get_about_me_service),
) -> list[ResumeView]:
    return [ResumeView.from_document(item) for item in (await service.get(current_user.id)).resumes]


@router.post("/resumes", response_model=ResumeView, status_code=201)
async def create_resume(
    resume: Annotated[UploadFile, File()],
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: AboutMeService = Depends(get_about_me_service),
) -> ResumeView:
    content = await resume.read(get_settings().max_resume_bytes + 1)
    try:
        return ResumeView.from_document(
            await service.add_resume(
                user_id=current_user.id,
                filename=resume.filename,
                content_type=resume.content_type,
                content=content,
            )
        )
    except ResumeValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.delete("/resumes/{document_id}", response_model=DeleteResult)
async def delete_resume(
    document_id: UUID,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: AboutMeService = Depends(get_about_me_service),
) -> DeleteResult:
    await _delete(lambda: service.delete_resume(current_user.id, document_id))
    return DeleteResult(deleted_id=document_id)


@router.get("/memories", response_model=list[MemoryView])
async def list_memories(
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: AboutMeService = Depends(get_about_me_service),
) -> list[MemoryView]:
    return [MemoryView.from_memory(item) for item in (await service.get(current_user.id)).memories]


@router.delete("/memories/{memory_id}", response_model=DeleteResult)
async def delete_memory(
    memory_id: UUID,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: AboutMeService = Depends(get_about_me_service),
) -> DeleteResult:
    await _delete(lambda: service.delete_memory(current_user.id, memory_id))
    return DeleteResult(deleted_id=memory_id)


async def _delete(operation) -> Response | None:
    try:
        await operation()
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return None
