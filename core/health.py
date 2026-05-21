from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Liveness/readiness probe: verifies the database and cache are reachable."""
    checks = {"db": False, "cache": False}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["db"] = True
    except Exception:
        pass
    try:
        cache.set("healthz", "1", 5)
        checks["cache"] = cache.get("healthz") == "1"
    except Exception:
        pass

    ok = all(checks.values())
    return JsonResponse(
        {"status": "ok" if ok else "degraded", **checks},
        status=200 if ok else 503,
    )
