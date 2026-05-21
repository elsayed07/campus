from ninja import Router

from apps.catalog import selectors
from shared.exceptions import NotFoundError

from ..schemas import CourseDetailOut, CourseOut

router = Router(tags=["courses"])


@router.get("/", response=list[CourseOut], auth=None)
def list_courses(request, q: str | None = None, subject: str | None = None):
    return selectors.published_courses(subject_slug=subject, search=q)


@router.get("/{slug}", response=CourseDetailOut, auth=None)
def get_course(request, slug: str):
    course = selectors.course_with_outline(slug=slug)
    if course is None or not course.is_published:
        raise NotFoundError("Course not found.")
    return course
