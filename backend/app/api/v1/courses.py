from fastapi import APIRouter, HTTPException, status

from app.course.catalog_v1 import COURSE_CATALOG_V1, COURSES_BY_ID
from app.course.schemas import CourseCatalogItem, CourseCatalogResponse

router = APIRouter()


@router.get("", response_model=CourseCatalogResponse)
def list_courses() -> CourseCatalogResponse:
    return CourseCatalogResponse(
        courses=tuple(CourseCatalogItem.from_definition(course) for course in COURSE_CATALOG_V1)
    )


@router.get("/{course_id}", response_model=CourseCatalogItem)
def get_course(course_id: str) -> CourseCatalogItem:
    course = COURSES_BY_ID.get(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
    return CourseCatalogItem.from_definition(course)
