import pytest

from apps.content.services import structure
from shared.exceptions import NotFoundError
from tests.factories import CourseFactory

pytestmark = pytest.mark.django_db


def test_positions_increment_on_add():
    course = CourseFactory()
    m0 = structure.add_module(course=course, title="One")
    m1 = structure.add_module(course=course, title="Two")
    assert (m0.position, m1.position) == (0, 1)

    l0 = structure.add_lesson(module=m0, title="L0")
    l1 = structure.add_lesson(module=m0, title="L1")
    assert (l0.position, l1.position) == (0, 1)


def test_reorder_modules_persists_new_order():
    course = CourseFactory()
    a = structure.add_module(course=course, title="A")
    b = structure.add_module(course=course, title="B")
    c = structure.add_module(course=course, title="C")

    structure.reorder_modules(course=course, ordered_ids=[str(c.id), str(a.id), str(b.id)])

    ordered = list(course.modules.values_list("title", flat=True))
    assert ordered == ["C", "A", "B"]


def test_add_content_item_rejects_unknown_kind():
    course = CourseFactory()
    module = structure.add_module(course=course, title="M")
    lesson = structure.add_lesson(module=module, title="L")
    with pytest.raises(NotFoundError):
        structure.add_content_item(lesson=lesson, kind="hologram")
