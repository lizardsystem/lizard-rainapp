# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf import settings
from django.conf.urls.defaults import handler404
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.contrib import admin
from django.http import HttpResponseServerError
from django.template import Context
from django.template import loader

admin.autodiscover()
handler404  # pyflakes

urlpatterns = patterns(
    '',
    url(r'^$',
        'lizard_fewsjdbc.views.homepage',
        {'template': 'lizard_rainapp/homepage.html'},
        name="lizard_rainapp.homepage",
        ),
    url(r'^fews_jdbc/(?P<jdbc_source_slug>.*)/$',
        'lizard_fewsjdbc.views.jdbc_source',
        {'adapter_class': 'adapter_rainapp',
         'filter_url_name': 'lizard_rainapp.jdbc_source'},
        name="lizard_rainapp.jdbc_source",
        ),
    url(r'^snippet_group/(?P<snippet_group_id>.*)/$',
        'lizard_rainapp.views.snippet_group_rainapp_bars',
        name='lizard_rainapp.snippet_group_rainapp_bars',
        ),
    url(r'^workspace_item/(?P<workspace_item_id>\d+)/$',
        'lizard_rainapp.views.workspace_item_rainapp_bars',
        name='lizard_rainapp.workspace_item_rainapp_bars',
        ),
    (r'^admin/', include(admin.site.urls)),
    )


if settings.DEBUG:
    # Add this also to the projects that use this application
    urlpatterns += patterns('',
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
