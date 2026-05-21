import pytest

from apps.catalog.services import courses as course_service
from apps.content.services import structure
from core.enums import CourseState
from shared.exceptions import ValidationError
from tests.factories import CourseFactory, InstructorFactory, SubjectFactory

pytestmark = pytest.mark.django_db


def test_create_course_generates_unique_slug():
    owner = InstructorFactory()
    subject = SubjectFactory()
    a = course_service.create_course(owner=owner, subject=subject, title="Intro to Go")
    b = course_service.create_course(owner=owner, subject=subject, title="Intro to Go")
    assert a.slug == "intro-to-go"
    assert b.slug == "intro-to-go-2"


def test_publish_requires_a_lesson():
    course = CourseFactory()
    with pytest.raises(ValidationError):
        course_service.publish_course(course=course)

    module = structure.add_module(course=course, title="Basics")
    structure.add_lesson(module=module, title="Welcome")

    published = course_service.publish_course(course=course)
    assert published.state == CourseState.PUBLISHED
    assert published.published_at is not None
