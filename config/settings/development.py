from .base import *  # noqa: F403
from .base import INSTALLED_APPS, MIDDLEWARE, STORAGES

DEBUG = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Plain static storage in dev: the manifest storage requires collectstatic and
# otherwise breaks admin's {% static %} tags under runserver.
STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
}

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.common.CommonMiddleware") + 1,
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)

INTERNAL_IPS = ["127.0.0.1"]
# Show the toolbar inside Docker where the request IP is not 127.0.0.1.
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG}
