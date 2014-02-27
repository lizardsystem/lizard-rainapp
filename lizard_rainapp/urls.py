# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from __future__ import absolute_import

from django.conf import settings
from django.conf.urls.defaults import handler404
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.contrib import admin
from django.http import HttpResponseServerError
from django.template import Context
from django.template import loader

from lizard_fewsjdbc.views import JdbcSourceView, HomepageView

from . import views

handler404  # pyflakes

urlpatterns = patterns(
    '',
    url(r'^$',
        HomepageView.as_view(template_name='lizard_rainapp/homepage.html'),
        name="lizard_rainapp.homepage",
        ),
    url(r'^fews_jdbc/(?P<jdbc_source_slug>.*)/$',
        JdbcSourceView.as_view(adapter_class='adapter_rainapp',
                               filter_url_name="lizard_rainapp.jdbc_source"),
        name="lizard_rainapp.jdbc_source",
        ),
    url(r'^beheer/$', views.AdminView.as_view(),
        name="lizard_rainapp_admin"),
    url(r'^beheer/rainappshape/(?P<slug>[^/]+)/$',
        views.DownloadShapeView.as_view(),
        name="lizard_rainapp_download_shape"),
    )


if getattr(settings, 'LIZARD_RAINAPP_STANDALONE', False):
    admin.autodiscover()
    urlpatterns += patterns(
        '',
        (r'^map/', include('lizard_map.urls')),
        (r'^admin/', include(admin.site.urls)),
        (r'', include('staticfiles.urls')),
    )


def handler500(request):
    """500 error handler which includes ``request`` in the context.

    Simple test:

      >>> handler500({})  #doctest: +ELLIPSIS
      <django.http.HttpResponseServerError object at ...>

    """
    t = loader.get_template('500.html')
    return HttpResponseServerError(
        t.render(Context({'request': request})))
