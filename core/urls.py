# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include  # add this
# from django.conf.urls import handler400, handler403, handler404, handler500

urlpatterns = [
    path('admin/', admin.site.urls),          
    path("auth/", include("authentication.urls")), # Auth routes - login / register
    path("", include("book.urls")),
    path('api/', include('Api.urls'))    
]


urlpatterns+= static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

handler400 = 'book.views.bad_request'
handler403 = 'book.views.permission_denied'
handler404 = 'book.views.page_not_found'
handler500 = 'book.views.server_error'
