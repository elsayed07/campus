from typing import Any

from .models import Event


def record_event(
    *,
    kind: str,
    actor=None,
    course=None,
    lesson=None,
    **metadata: Any,
) -> Event:
    """Append an analytics event. Cheap insert; callers fire-and-forget."""
    return Event.objects.create(
        kind=kind,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        course=course,
        lesson=lesson,
        metadata=metadata or {},
    )
