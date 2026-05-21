from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def group_send(group: str, message: dict[str, Any]) -> None:
    """Fan a message out to a channel-layer group from synchronous code.

    `message` must include a `type` key naming the consumer handler method
    (dots become underscores, e.g. `chat.message` → `chat_message`).
    """
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(group, message)


def user_group(user_id) -> str:
    return f"notifications_{user_id}"


def chat_group(course_id) -> str:
    return f"chat_{course_id}"
