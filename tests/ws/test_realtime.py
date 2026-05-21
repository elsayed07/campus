import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from apps.chat.consumers import ChatConsumer
from apps.notifications.consumers import NotificationConsumer
from core.enums import CourseState
from shared import realtime
from tests.factories import CourseFactory, UserFactory


@database_sync_to_async
def _make_user():
    return UserFactory()


@database_sync_to_async
def _make_enrolled():
    from apps.enrollment.services import enrolling

    course = CourseFactory(state=CourseState.PUBLISHED)
    student = UserFactory()
    enrolling.enroll(student=student, course=course)
    return course, student


@pytest.mark.django_db(transaction=True)
async def test_notification_socket_receives_push():
    user = await _make_user()
    communicator = WebsocketCommunicator(
        NotificationConsumer.as_asgi(), "/ws/notifications/"
    )
    communicator.scope["user"] = user
    connected, _ = await communicator.connect()
    assert connected

    await database_sync_to_async(realtime.group_send)(
        realtime.user_group(user.id),
        {"type": "notify", "payload": {"title": "Ping", "unread": 2}},
    )
    message = await communicator.receive_json_from()
    assert message["title"] == "Ping"
    assert message["unread"] == 2
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_unauthenticated_notification_socket_is_rejected():
    from django.contrib.auth.models import AnonymousUser

    communicator = WebsocketCommunicator(
        NotificationConsumer.as_asgi(), "/ws/notifications/"
    )
    communicator.scope["user"] = AnonymousUser()
    connected, _ = await communicator.connect()
    assert connected is False


@pytest.mark.django_db(transaction=True)
async def test_chat_socket_round_trip():
    course, student = await _make_enrolled()
    communicator = WebsocketCommunicator(
        ChatConsumer.as_asgi(), f"/ws/chat/{course.slug}/"
    )
    communicator.scope["user"] = student
    communicator.scope["url_route"] = {"kwargs": {"slug": course.slug}}
    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({"body": "hello world"})
    message = await communicator.receive_json_from()
    assert message["body"] == "hello world"
    assert message["author"] == student.display_name
    await communicator.disconnect()
