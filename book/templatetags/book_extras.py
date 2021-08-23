from django import template
from django.db.models.aggregates import Count
from ..models import UserActivity
from django.utils import timezone
import math
import datetime
import requests
from django.template.loader import get_template

register = template.Library()

@register.inclusion_tag('book/inclusions/_pagination.html', takes_context=True)
def show_pagination(context):
    return {
        'page_objects':context['objects'],
        'search':context['search'],
        'orderby':context['orderby'],}

@register.inclusion_tag('book/inclusions/_messages.html',takes_context=True)
def show_messages(context):
        return {'messages':context['messages'],}
    
    
@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    """
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()

@register.inclusion_tag('book/inclusions/_weather.html',takes_context=True)
def show_weather(context):
    url = 'http://api.openweathermap.org/data/2.5/weather?q=Paris,fr&units=imperial&appid=2e37fd2364d867821f298280137eecc0'
    r = requests.get(url).json()
    paris_weather={}

    if r['cod']==200:
        paris_weather = {
        'city':'Paris',
        'temperature' :float("{0:.2f}".format((r['main']['temp']-32)* 5/9)),
        'description' : r['weather'][0]['description'],
        'icon' : r['weather'][0]['icon'],
        'country':r['sys']['country']}

    return {'paris_weather':paris_weather}


@register.filter(name='timesince')
def timesince(date):
    now = timezone.now()
    diff = now - date

    if diff.days == 0 and diff.seconds >= 0 and diff.seconds < 60:
        return ' just now'
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

@register.filter('has_group')
def has_group(user, group_name):
    groups = user.groups.all().values_list('name', flat=True)
    return True if group_name in groups else False

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
