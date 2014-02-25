# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Views for the RainApp, mostly a page to upload new region shapefiles."""

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import logging

from django.http import HttpResponseRedirect
from django.contrib.gis.geos import GEOSGeometry
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from lizard_ui.views import ViewContextMixin

from . import forms
from . import models

logger = logging.getLogger(__name__)


class AdminView(ViewContextMixin, TemplateView):
    template_name = "lizard_rainapp/admin.html"

    def get(self, request):
        self.form = forms.UploadShapefileForm()
        return super(AdminView, self).get(request)

    def post(self, request):
        self.form = forms.UploadShapefileForm(
            request.POST, request.FILES)

        if self.form.is_valid():
            self.save_shape()
            self.form.clean_temporary_directory()
            return HttpResponseRedirect(
                reverse("lizard_rainapp_admin"))
        else:
            return super(AdminView, self).get(request)

    def get_field(self, feature, fieldname, default=None):
        try:
            name = self.form.cleaned_data[fieldname]
            return feature.GetField(
                feature.GetFieldIndex(name.encode('utf8')))
        except ValueError:
            return default

    def save_shape(self):
        rainappconfig = self.form.cleaned_data['config']
        # First, delete old data
        models.GeoObject.objects.filter(
            config=rainappconfig).delete()

        shapefile = self.form.open_shapefile()

        layer = shapefile.GetLayer()

        num_features = 0

        for feature in layer:
            geom = feature.GetGeometryRef()

            models.GeoObject.objects.create(
                municipality_id=self.get_field(feature, 'id_field'),
                name=self.get_field(feature, 'name_field'),
                x=self.get_field(feature, 'x_field'),
                y=self.get_field(feature, 'y_field'),
                area=self.get_field(feature, 'area_field'),
                geometry=GEOSGeometry(geom.ExportToWkt(), srid=4326),
                config=rainappconfig)
            num_features += 1

        logger.debug("Added {} features.".format(num_features))
