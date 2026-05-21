from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer

from apps.catalog.models import Course
from shared import realtime
from shared.exceptions import DomainError

from . import services


class ChatConsumer(JsonWebsocketConsumer):
    """Realtime course chat. Thin transport: all logic lives in chat.services.

    A synchronous consumer, so the handler runs in a worker thread where direct
    ORM access is safe.
    """

    def connect(self):
        user = self.scope.get("user")
        slug = self.scope["url_route"]["kwargs"]["slug"]
        self.course = Course.objects.filter(slug=slug).first()
        if self.course is None or not services.can_participate(
            user=user, course=self.course
        ):
            self.close()
            return
        self.group = realtime.chat_group(self.course.id)
        async_to_sync(self.channel_layer.group_add)(self.group, self.channel_name)
        self.accept()

    def disconnect(self, code):
        group = getattr(self, "group", None)
        if group:
            async_to_sync(self.channel_layer.group_discard)(group, self.channel_name)

    def receive_json(self, content, **kwargs):
        try:
            services.post_message(
                course=self.course,
                author=self.scope["user"],
                body=content.get("body", ""),
            )
        except DomainError as exc:
            self.send_json({"error": exc.message})

    def chat_message(self, event):
        self.send_json(event["payload"])
