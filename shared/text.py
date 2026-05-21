from django.db.models import Model
from django.utils.text import slugify


def unique_slug(model: type[Model], value: str, field: str = "slug") -> str:
    """Return a slug for `value` that is unique for `model.field`."""
    base = slugify(value) or "item"
    candidate = base
    suffix = 2
    while model._default_manager.filter(**{field: candidate}).exists():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate
