import bleach
import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_ALLOWED_TAGS = [
    "p", "br", "strong", "em", "u", "code", "pre", "blockquote",
    "ul", "ol", "li", "h1", "h2", "h3", "h4", "a", "img", "hr", "table",
    "thead", "tbody", "tr", "th", "td",
]
_ALLOWED_ATTRS = {"a": ["href", "title"], "img": ["src", "alt"]}


@register.filter
def markdownify(text: str) -> str:
    if not text:
        return ""
    html = md.markdown(text, extensions=["fenced_code", "tables"])
    cleaned = bleach.clean(html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS)
    return mark_safe(cleaned)
