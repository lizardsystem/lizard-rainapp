# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Views for the RainApp, mostly a page to upload new region shapefiles."""

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import io
import logging
import operator
import os
import shutil
import tempfile
import zipfile

import shapefile

from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.views.generic import View
from lizard_ui.views import ViewContextMixin

from . import forms
from . import models

logger = logging.getLogger(__name__)


class AdminView(ViewContextMixin, TemplateView):
    template_name = "lizard_rainapp/admin.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('lizard_rainapp.change_geoobject'):
            raise PermissionDenied()
        return super(AdminView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        self.form = forms.UploadShapefileForm()
        return super(AdminView, self).get(request)

    def post(self, request):
        self.form = forms.UploadShapefileForm(
            request.POST, request.FILES)

        if not self.form.is_valid():
            return super(AdminView, self).get(request)

        try:
            self.save_shape()
        finally:
            self.form.clean_temporary_directory()
        return HttpResponseRedirect(
            reverse("lizard_rainapp_admin"))

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

        shape = self.form.open_shapefile()
        layer = shape.GetLayer()

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

    def rainapp_configs(self):
        return models.RainappConfig.objects.all()


class DownloadShapeView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('lizard_rainapp.change_geoobject'):
            raise PermissionDenied()
        return super(DownloadShapeView, self).dispatch(
            request, *args, **kwargs)

    def get(self, request, slug):
        try:
            rainappconfig = models.RainappConfig.objects.get(
                slug=slug)
        except models.RainappConfig.DoesNotExist:
            raise Http404()

        if not rainappconfig.has_geoobjects:
            raise Http404()

        bytebuffer = self.save_data_to_zip(rainappconfig)

        # Setup HTTPResponse for returning a zip file
        response = HttpResponse(content_type='application/zip')
        response['Content-Disposition'] = (
            'attachment; filename={}.zip'.format(slug))

        response.write(bytebuffer.read())

        return response

    def save_data_to_zip(self, rainappconfig):
        # Save a shapefile to a temp directory
        temp_dir = tempfile.mkdtemp()

        try:
            shapefile_path = os.path.join(
                temp_dir, rainappconfig.slug)

            shp = shapefile.Writer(shapefile.POLYGON)

            shp.field(b'ID_NS')
            shp.field(b'ID')
            shp.field(b'X', b'F', 11, 5)
            shp.field(b'Y', b'F', 11, 5)
            shp.field(b'AREA', b'F', 11, 5)

            for geo in models.GeoObject.objects.filter(config=rainappconfig):
                if str(geo.geometry).startswith('MULTIPOLYGON'):
                    # For pyshp, multipolygons are basically normal
                    # polygons with all the parts after each other. Meaning
                    # we need to add them together them by hand.
                    geometry = [
                        [list(l) for l in polygon] for polygon in geo.geometry]
                    geometry = reduce(operator.add, geometry, [])
                else:
                    geometry = [list(l) for l in geo.geometry]

                shp.poly(parts=geometry)
                shp.record(
                    geo.municipality_id,
                    geo.name,
                    geo.x,
                    geo.y,
                    geo.area)

            shp.save(shapefile_path)

            # Create a zipfile in a BytesIO buffer
            bytebuffer = io.BytesIO()
            zipf = zipfile.ZipFile(bytebuffer, 'w', zipfile.ZIP_DEFLATED)
            for filename in os.listdir(temp_dir):
                zipf.write(os.path.join(temp_dir, filename), filename)
            zipf.close()
            bytebuffer.seek(0)

            return bytebuffer
        finally:
            # Remove temporary directory
            shutil.rmtree(temp_dir)
