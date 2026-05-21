import factory

from apps.enrollment.models import Enrollment

from .catalog import CourseFactory
from .users import UserFactory


class EnrollmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Enrollment

    student = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
