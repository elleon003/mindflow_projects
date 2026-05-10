from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from two_factor.urls import urlpatterns as tf_urls

from mindflow.api import api as mindflow_api
from mindflow import views as mindflow_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', mindflow_api.urls),
    path('capture/', mindflow_views.capture, name='capture'),
    path(
        'capture/organize/start/',
        mindflow_views.capture_organize_start,
        name='capture_organize_start',
    ),
    path(
        'capture/organize/<int:session_id>/',
        mindflow_views.capture_organize_session,
        name='capture_organize_session',
    ),
    path(
        'capture/inbox/<int:item_id>/discard/',
        mindflow_views.capture_discard_item,
        name='capture_discard_item',
    ),
    path('', include(tf_urls)),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
        path('__reload__/', include('django_browser_reload.urls')),
    ]