from django.urls import URLPattern

# WebSocket routes are registered here as realtime apps come online
# (chat + notifications in Phase 5).
websocket_urlpatterns: list[URLPattern] = []
