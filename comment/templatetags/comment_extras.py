"""Template filters for comment HTML."""

from django import template
from django.utils.safestring import mark_safe

from comment.sanitize import sanitize_comment_html  # absolute: templatetags load before package relative resolution in some setups

register = template.Library()


@register.filter(name="sanitize_rich_text")
def sanitize_rich_text(value):
    """Render CKEditor HTML after bleach has removed unsafe markup."""
    return mark_safe(sanitize_comment_html(value))
