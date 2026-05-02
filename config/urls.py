from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from two_factor.urls import urlpatterns as tf_urls

from mindflow.api import api as mindflow_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', mindflow_api.urls),
    path('', include(tf_urls)),
    
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
        path('__reload__/', include('django_browser_reload.urls')),
    ]