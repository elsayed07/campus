import factory
from django.contrib.auth import get_user_model

from apps.accounts.models import Profile
from core.enums import Role

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@campus.test")
    full_name = factory.Faker("name")
    role = Role.STUDENT

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or "Test1234!pw")
        self.save()


class InstructorFactory(UserFactory):
    role = Role.INSTRUCTOR


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    headline = factory.Faker("sentence", nb_words=4)
