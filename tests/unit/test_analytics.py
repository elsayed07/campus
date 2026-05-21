import pytest
from django.utils import timezone

from apps.analytics import selectors
from apps.analytics.models import CourseDailyStat, Event
from apps.analytics.tasks import rollup_daily_stats
from apps.content.services import structure
from apps.enrollment.services import enrolling
from apps.progress.services import tracking
from core.enums import CourseState, EventKind
from tests.factories import CourseFactory, InstructorFactory, UserFactory

pytestmark = pytest.mark.django_db


def _course(instructor=None):
    course = CourseFactory(
        state=CourseState.PUBLISHED, owner=instructor or InstructorFactory()
    )
    module = structure.add_module(course=course, title="M")
    lesson = structure.add_lesson(module=module, title="L")
    return course, lesson


def test_enroll_and_completion_emit_events(django_capture_on_commit_callbacks):
    course, lesson = _course()
    student = UserFactory()
    enrolling.enroll(student=student, course=course)
    assert Event.objects.filter(kind=EventKind.ENROLL, course=course).count() == 1

    enrollment = course.enrollments.get(student=student)
    with django_capture_on_commit_callbacks(execute=True):
        tracking.mark_lesson_complete(enrollment=enrollment, lesson=lesson)
    assert Event.objects.filter(kind=EventKind.LESSON_COMPLETE, course=course).exists()
    assert Event.objects.filter(kind=EventKind.COURSE_COMPLETE, course=course).exists()


def test_course_funnel_counts():
    course, lesson = _course()
    student = UserFactory()
    Event.objects.create(kind=EventKind.COURSE_VIEW, course=course)
    enrolling.enroll(student=student, course=course)
    tracking.mark_lesson_complete(enrollment=course.enrollments.get(student=student), lesson=lesson)

    funnel = selectors.course_funnel(course=course)
    assert funnel["enrollments"] == 1
    assert funnel["started"] == 1
    assert funnel["completed"] == 1
    assert funnel["completion_rate"] == 100


def test_instructor_overview_aggregates():
    instructor = InstructorFactory()
    course, lesson = _course(instructor)
    student = UserFactory()
    enrolling.enroll(student=student, course=course)
    tracking.mark_lesson_complete(enrollment=course.enrollments.get(student=student), lesson=lesson)

    overview = selectors.instructor_overview(user=instructor)
    assert overview["total_enrollments"] == 1
    assert overview["total_completions"] == 1
    assert overview["active_learners_7d"] == 1


def test_rollup_writes_daily_stats():
    course, _lesson = _course()
    student = UserFactory()
    enrolling.enroll(student=student, course=course)

    today = timezone.localdate().isoformat()
    written = rollup_daily_stats(for_date=today)
    assert written >= 1
    stat = CourseDailyStat.objects.get(course=course, date=today)
    assert stat.new_enrollments == 1
    assert stat.event_count >= 1
