import factory

from apps.catalog.models import Course, Subject
from core.enums import CourseState, PricingModel

from .users import InstructorFactory


class SubjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subject
        django_get_or_create = ["name"]

    name = factory.Sequence(lambda n: f"Subject {n}")


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course

    owner = factory.SubFactory(InstructorFactory)
    subject = factory.SubFactory(SubjectFactory)
    title = factory.Sequence(lambda n: f"Course {n}")
    slug = factory.Sequence(lambda n: f"course-{n}")
    headline = factory.Faker("sentence", nb_words=6)
    pricing_model = PricingModel.FREE
    state = CourseState.DRAFT
