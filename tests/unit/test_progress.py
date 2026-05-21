import pytest

from apps.content.services import structure
from apps.enrollment.services import enrolling
from apps.progress import selectors
from apps.progress.services import tracking
from core.enums import CourseState, EnrollmentStatus, ProgressionMode
from tests.factories import CourseFactory, UserFactory

pytestmark = pytest.mark.django_db


def _course_with_lessons(n=3, mode=ProgressionMode.SEQUENTIAL):
    course = CourseFactory(state=CourseState.PUBLISHED, progression_mode=mode)
    module = structure.add_module(course=course, title="Module 1")
    lessons = [structure.add_lesson(module=module, title=f"L{i}") for i in range(n)]
    return course, lessons


def test_sequential_locks_until_previous_complete():
    course, lessons = _course_with_lessons(3)
    student = UserFactory()
    enrollment = enrolling.enroll(student=student, course=course)

    room = selectors.build_classroom(enrollment=enrollment)
    unlocked = {n.lesson.id for m in room.modules for n in m.lessons if n.unlocked}
    assert lessons[0].id in unlocked
    assert lessons[1].id not in unlocked

    tracking.mark_lesson_complete(enrollment=enrollment, lesson=lessons[0])
    room = selectors.build_classroom(enrollment=enrollment)
    unlocked = {n.lesson.id for m in room.modules for n in m.lessons if n.unlocked}
    assert lessons[1].id in unlocked
    assert lessons[2].id not in unlocked


def test_open_mode_unlocks_everything():
    course, lessons = _course_with_lessons(3, mode=ProgressionMode.OPEN)
    enrollment = enrolling.enroll(student=UserFactory(), course=course)
    room = selectors.build_classroom(enrollment=enrollment)
    unlocked = {n.lesson.id for m in room.modules for n in m.lessons if n.unlocked}
    assert all(lesson.id in unlocked for lesson in lessons)


def test_completing_all_lessons_completes_enrollment():
    course, lessons = _course_with_lessons(2)
    enrollment = enrolling.enroll(student=UserFactory(), course=course)
    for lesson in lessons:
        tracking.mark_lesson_complete(enrollment=enrollment, lesson=lesson)
    enrollment.refresh_from_db()
    assert enrollment.progress_percent == 100
    assert enrollment.status == EnrollmentStatus.COMPLETED
    assert enrollment.completed_at is not None


def test_progress_percent_is_partial():
    course, lessons = _course_with_lessons(4)
    enrollment = enrolling.enroll(student=UserFactory(), course=course)
    tracking.mark_lesson_complete(enrollment=enrollment, lesson=lessons[0])
    enrollment.refresh_from_db()
    assert enrollment.progress_percent == 25


def test_locked_lesson_is_not_accessible():
    course, lessons = _course_with_lessons(3)
    enrollment = enrolling.enroll(student=UserFactory(), course=course)
    assert selectors.accessible_lesson(enrollment=enrollment, lesson_id=lessons[2].id) is None
    assert selectors.accessible_lesson(enrollment=enrollment, lesson_id=lessons[0].id) is not None


def test_build_classroom_is_not_n_plus_1(django_assert_max_num_queries):
    course, _ = _course_with_lessons(12)
    enrollment = enrolling.enroll(student=UserFactory(), course=course)
    # Modules + lessons (prefetch) + completed ids — constant regardless of size.
    with django_assert_max_num_queries(4):
        room = selectors.build_classroom(enrollment=enrollment)
        _ = [n.lesson.title for m in room.modules for n in m.lessons]
