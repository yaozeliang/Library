"""Strip unsafe HTML from reader-authored rich text before it is rendered."""

import bleach

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "blockquote",
    "a",
    "ol",
    "ul",
    "li",
    "span",
    "pre",
    "code",
    "h1",
    "h2",
    "h3",
    "h4",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "span": ["style"],
}

ALLOWED_STYLES = ["color", "background-color", "font-weight"]


def sanitize_comment_html(value):
    """Return comment HTML with scripts and other unsafe markup removed."""
    if not value:
        return ""
    return bleach.clean(
        str(value),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        styles=ALLOWED_STYLES,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
