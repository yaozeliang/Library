from django import template
from django.db.models.aggregates import Count
from ..models import UserActivity
from django.utils import timezone
import math
import datetime
import requests

register = template.Library()


@register.inclusion_tag('book/inclusions/_logs_pagination.html', takes_context=True)
def show_logs_pagination(context):
    return {
        'page_objects':context['activities'],
    }



# @register.inclusion_tag('article/inclusions/_notification.html',takes_context=True)
# def show_notification(context):
#     url = 'http://api.openweathermap.org/data/2.5/weather?q=Paris,fr&units=imperial&appid=2e37fd2364d867821f298280137eecc0'
#     r = requests.get(url).json()
#     paris_weather={}

#     if r['cod']==200:
#         paris_weather = {
#         'city':'Paris',
#         'temperature' :float("{0:.2f}".format((r['main']['temp']-32)* 5/9)),
#         'description' : r['weather'][0]['description'],
#         'icon' : r['weather'][0]['icon'],
#         'country':r['sys']['country']}

#     return {'paris_weather':paris_weather}



# @register.filter(name='timesince_zh')
# def time_since_zh(value):
#     now = timezone.now()
#     diff = now - value

#     if diff.days == 0 and diff.seconds >= 0 and diff.seconds < 60:
#         return '刚刚'

#     if diff.days == 0 and diff.seconds >= 60 and diff.seconds < 3600:
#         return str(math.floor(diff.seconds / 60)) + "分钟前"

#     if diff.days == 0 and diff.seconds >= 3600 and diff.seconds < 86400:
#         return str(math.floor(diff.seconds / 3600)) + "小时前"

#     if diff.days >= 1 and diff.days < 30:
#         return str(diff.days) + "天前"

#     if diff.days >= 30 and diff.days < 365:
#         return str(math.floor(diff.days / 30)) + "个月前"

#     if diff.days >= 365:
#         return str(math.floor(diff.days / 365)) + "年前"


