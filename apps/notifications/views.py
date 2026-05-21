from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import selectors, services
from .models import Notification


@login_required
def inbox(request):
    notifications = selectors.recent(user=request.user, limit=50)
    return render(
        request, "notifications/inbox.html", {"notifications": notifications}
    )


@login_required
@require_POST
def read_all(request):
    services.mark_all_read(user=request.user)
    return redirect("notifications:inbox")


@login_required
@require_POST
def read_one(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    services.mark_read(notification=notification)
    return redirect(notification.url or "notifications:inbox")
