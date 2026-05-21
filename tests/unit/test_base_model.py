import pytest

from tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_user_has_uuid_primary_key():
    user = UserFactory()
    assert user.id is not None
    assert "-" in str(user.id)


def test_soft_delete_hides_from_default_manager():
    from apps.accounts.models import Profile

    user = UserFactory()
    profile = user.profile
    profile_id = profile.id

    profile.delete()

    assert profile.deleted_at is not None
    assert not Profile.objects.filter(id=profile_id).exists()
    assert Profile.all_objects.filter(id=profile_id).exists()


def test_soft_delete_restore():
    from apps.accounts.models import Profile

    profile = UserFactory().profile
    profile.delete()
    profile.restore()

    assert profile.deleted_at is None
    assert Profile.objects.filter(id=profile.id).exists()
