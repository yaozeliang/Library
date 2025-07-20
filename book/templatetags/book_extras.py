"""Template tags for the book app."""

import datetime
import math
from typing import Any, Dict

import requests
from django import template
from django.utils import timezone

register = template.Library()


@register.inclusion_tag("book/inclusions/_pagination.html", takes_context=True)
def show_pagination(context: Dict[str, Any]) -> Dict[str, Any]:
    """Show pagination template tag.

    Args:
        context: Template context.

    Returns:
        Dictionary with pagination data.
    """
    return {
        "page_objects": context["objects"],
        "search": context["search"],
        "orderby": context["orderby"],
    }


@register.inclusion_tag("book/inclusions/_messages.html", takes_context=True)
def show_messages(context: Dict[str, Any]) -> Dict[str, Any]:
    """Show messages template tag.

    Args:
        context: Template context.

    Returns:
        Dictionary with messages.
    """
    return {"messages": context["messages"]}


@register.simple_tag(takes_context=True)
def param_replace(context: Dict[str, Any], **kwargs: Any) -> str:
    """Replace URL parameters.

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278

    Args:
        context: Template context.
        **kwargs: URL parameters to replace.

    Returns:
        URL encoded string.
    """
    d = context["request"].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()


@register.inclusion_tag("book/inclusions/_weather.html", takes_context=True)
def show_weather(context: Dict[str, Any]) -> Dict[str, Any]:
    """Show weather template tag.

    Args:
        context: Template context.

    Returns:
        Dictionary with weather data.
    """
    url = "http://api.openweathermap.org/data/2.5/weather?q=Paris,fr&units=imperial&appid=2e37fd2364d867821f298280137eecc0"
    try:
        r = requests.get(url, timeout=5).json()
        paris_weather = {}

        if r["cod"] == 200:
            paris_weather = {
                "city": "Paris",
                "temperature": float(
                    "{0:.2f}".format((r["main"]["temp"] - 32) * 5 / 9)
                ),
                "description": r["weather"][0]["description"],
                "icon": r["weather"][0]["icon"],
                "country": r["sys"]["country"],
            }
    except (requests.RequestException, KeyError):
        paris_weather = {}

    return {"paris_weather": paris_weather}


@register.filter(name="timesince")
def timesince(date: datetime.datetime) -> str:
    """Calculate time since a given date.

    Args:
        date: Date to calculate time since.

    Returns:
        Human readable time string.
    """
    now = timezone.now()
    diff = now - date

    if diff.days == 0 and diff.seconds >= 0 and diff.seconds < 60:
        return " just now"
    if diff.days == 0 and diff.seconds >= 60 and diff.seconds < 3600:
        return str(math.floor(diff.seconds / 60)) + " minutes ago"
    if diff.days == 0 and diff.seconds >= 3600 and diff.seconds < 86400:
        return str(math.floor(diff.seconds / 3600)) + " hours ago"
    if diff.days == 1 and diff.days < 30:
        return str(diff.days) + " day ago"
    if diff.days >= 1 and diff.days < 30:
        return str(diff.days) + " days ago"
    if diff.days >= 30 and diff.days < 365:
        return str(math.floor(diff.days / 30)) + " months ago"
    if diff.days >= 365:
        return str(math.floor(diff.days / 365)) + " years ago"
    return ""


@register.filter("has_group")
def has_group(user: Any, group_name: str) -> bool:
    """Check if user has a specific group.

    Args:
        user: User object.
        group_name: Name of the group to check.

    Returns:
        True if user has the group, False otherwise.
    """
    groups = user.groups.all().values_list("name", flat=True)
    return group_name in groups


@register.filter
def get_item(dictionary: Dict[str, Any], key: str) -> Any:
    """Get item from dictionary.

    Args:
        dictionary: Dictionary to get item from.
        key: Key to look up.

    Returns:
        Value from dictionary or None.
    """
    return dictionary.get(key)
