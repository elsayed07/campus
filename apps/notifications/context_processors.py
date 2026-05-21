from . import selectors


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {"unread_notifications": 0}
    return {"unread_notifications": selectors.unread_count(user=request.user)}
