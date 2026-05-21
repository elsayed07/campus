from typing import Any

from django.core.paginator import Paginator
from django.db.models import QuerySet

DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 100


def paginate(qs: QuerySet, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> dict[str, Any]:
    """Paginate a queryset into a template/JSON-friendly dict."""
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)
    return {
        "items": list(page_obj.object_list),
        "page": page_obj.number,
        "page_size": page_size,
        "num_pages": paginator.num_pages,
        "total": paginator.count,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
        "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
    }
