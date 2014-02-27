# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

"""Forms for RainApp. Currently only one, for uploading shapefiles to
fill the GeoObject model."""

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os
import shutil
import tempfile

import osgeo.ogr

from django import forms

from . import models


class UploadShapefileForm(forms.Form):
    """Note: if this form is valid, then a temporary directory with an
    uploaded shapefile will have been created. Call
    form.clean_temporary_directory after using the form!

    The path to the (.shp part of the) shapefile will be in
    cleaned_data['shp_file_path']."""

    config = forms.ModelChoiceField(
        label="Rainapp Config",
        queryset=models.RainappConfig.objects.all())

    id_field = forms.CharField(
        label='"ID" veld',
        help_text=(
            "Veld in de shapefile waar het FEWS ID van het " +
            "deelgebied in staat."),
        initial="ID_NS",
        required=True)

    name_field = forms.CharField(
        label='"NAME" veld',
        help_text=(
            "Veld in de shapefile waar de naam van het deelgebied " +
            "(te zien in de interface) in staat."),
        initial="ID",
        required=True)

    x_field = forms.CharField(
        label='"X" veld',
        help_text=(
            "Veld in de shapefile waar de Rijksdriehoek X coördinaat " +
            "van het zwaartepunt van het deelgebied in staat."),
        initial="X",
        required=True)

    y_field = forms.CharField(
        label='"Y" veld',
        help_text=(
            "Veld in de shapefile waar de Rijksdriehoek Y coördinaat " +
            "van het zwaartepunt van het deelgebied in staat."),
        initial="Y",
        required=True)

    area_field = forms.CharField(
        label='"AREA" veld',
        help_text=(
            "Veld in de shapefile waar de oppervlakte van het " +
            "deelgebied in staat."),
        initial="AREA",
        required=True)

    shp_file = forms.FileField(
        label=".shp file",
        required=True)

    dbf_file = forms.FileField(
        label=".dbf file",
        required=True)

    shx_file = forms.FileField(
        label=".shx file",
        required=True)

    @property
    def temporary_directory(self):
        if not hasattr(self, '_temporary_directory'):
            self._temporary_directory = tempfile.mkdtemp()
        return self._temporary_directory

    def save_file(self, fieldname):
        uploadedfile = self.cleaned_data.get(fieldname)
        if uploadedfile is None:
            return

        filename = os.path.join(self.temporary_directory, uploadedfile.name)
        with open(filename, 'wb') as f:
            for chunk in uploadedfile.chunks():
                f.write(chunk)
        self.cleaned_data[fieldname + '_path'] = filename

    def add_field_error(self, field, message):
        """Assumes this field has no errors yet"""
        self._errors[field] = self.error_class([message])

    def open_shapefile(self):
        if not hasattr(self, '_shapefile'):
            self._shapefile = osgeo.ogr.Open(
                self.cleaned_data['shp_file_path'].encode('utf8'))
        return self._shapefile

    def check_fields_exist(self):
        shapefile = self.open_shapefile()
        if shapefile is None:
            self.add_field_error('shp_file', "Kan de shapefile niet openen.")
            return

        if shapefile.GetLayerCount() < 1:
            self.add_field_error('shp_file', "Shapefile heeft geen layers.")
            return

        layer = shapefile.GetLayer(0)
        if layer.GetFeatureCount() < 1:
            self.add_field_error(
                'shp_file', "Shapefile layer heeft geen features.")
            return

        feature = layer.GetFeature(0)
        for field_name in ('id_field', 'name_field', 'x_field', 'y_field',
                           'area_field'):
            shape_field = self.cleaned_data.get(field_name)
            if not shape_field:
                continue  # Will have led to an error elsewhere
            shape_field = shape_field.encode('utf8')  # For osgeo
            try:
                feature.GetField(shape_field)
            except ValueError:
                self.add_field_error(field_name,
                    "Shapefile heeft geen veld '{}'.".format(shape_field))
                return

    def clean(self):
        super(UploadShapefileForm, self).clean()
        self.cleaned_data['temporary_directory'] = self.temporary_directory

        self.save_file('shp_file')
        self.save_file('dbf_file')
        self.save_file('shx_file')

        if self.cleaned_data.get('shp_file_path'):
            self.check_fields_exist()

        return self.cleaned_data

    def clean_temporary_directory(self):
        if os.path.exists(self.temporary_directory):
            shutil.rmtree(self.temporary_directory)
