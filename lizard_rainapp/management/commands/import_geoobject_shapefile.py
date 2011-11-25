# -*- coding: utf-8 -*-
# Copyright 2011 Nelen & Schuurmans
import logging

from pkg_resources import resource_filename
from osgeo import ogr
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from lizard_map import coordinates

from lizard_rainapp.models import GeoObject

logger = logging.getLogger(__name__)


def load_shapefile():
    shapefile_filename = getattr(settings, 'RAINAPP_SHAPEFILE', 
                                 resource_filename('lizard_rainapp',
                                                   'shape/gemeenten2009.shp'))
    # original_srs = ogr.osr.SpatialReference()
    # original_srs.ImportFromProj4(coordinates.RD)
    # target_srs = ogr.osr.SpatialReference()
    # target_srs.ImportFromEPSG(4326)
    # coordinate_transformation = ogr.osr.CoordinateTransformation(
    #     original_srs, target_srs)

    drv = ogr.GetDriverByName('ESRI Shapefile')
    source = drv.Open(shapefile_filename)

    if source is None:
        raise ValueError("Shapefile not found. Set RAINAPP_SHAPEFILE in settings.")

    layer = source.GetLayer()

    if GeoObject.objects.count():
        logger.info("First deleting the existing geoobjects...")
        GeoObject.objects.all().delete()

    logger.info("Importing new geoobjects...")
    number_of_features = 0

    for feature in layer:
        geom = feature.GetGeometryRef()
        # Optional extra things to do with the shape
        # geom.Transform(coordinate_transformation)
        # geom.FlattenTo2D()
        # import pdb;pdb.set_trace()

        id_field = getattr(settings, 'RAINAPP_ID_FIELD', 'ID')
        name_field = getattr(settings, 'RAINAPP_NAME_FIELD', 'NAME')
        code_field = getattr(settings, 'RAINAPP_CODE_FIELD', 'GEM_CODE')
        x_field = getattr(settings, 'RAINAPP_X_FIELD', 'X')
        y_field = getattr(settings, 'RAINAPP_Y_FIELD', 'Y')
        area_field = getattr(settings, 'RAINAPP_AREA_FIELD', 'OPP')

        def get_field(fieldname, default=None):
            try:
                return feature.GetField(feature.GetFieldIndex(fieldname))
            except ValueError:
                return default

        kwargs = {
            'municipality_id': get_field(id_field),
            'name': get_field(name_field),
            'code': get_field(code_field),
            'x': get_field(x_field),
            'y': get_field(y_field),
            'area': get_field(area_field, -1),
            'geometry': GEOSGeometry(geom.ExportToWkt(), srid=4326),
        }
        geoobject = GeoObject(**kwargs)
        geoobject.save()
        number_of_features += 1
    logger.info("Added %s polygons.", number_of_features)


class Command(BaseCommand):
    args = ""
    help = "TODO"

    def handle(self, *args, **options):
        load_shapefile()
