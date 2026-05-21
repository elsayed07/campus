from channels.generic.websocket import JsonWebsocketConsumer

from shared import realtime


class NotificationConsumer(JsonWebsocketConsumer):
    """Per-user channel that receives live notification pushes."""

    def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            self.close()
            return
        self.group = realtime.user_group(user.id)
        self.groups_joined = [self.group]
        from asgiref.sync import async_to_sync

        async_to_sync(self.channel_layer.group_add)(self.group, self.channel_name)
        self.accept()

    def disconnect(self, code):
        group = getattr(self, "group", None)
        if group:
            from asgiref.sync import async_to_sync

            async_to_sync(self.channel_layer.group_discard)(group, self.channel_name)

    def notify(self, event):
        self.send_json(event["payload"])
