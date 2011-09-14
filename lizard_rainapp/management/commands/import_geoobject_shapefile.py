# -*- coding: utf-8 -*-
# Copyright 2011 Nelen & Schuurmans
import logging

from pkg_resources import resource_filename
from osgeo import ogr
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from lizard_map import coordinates
from lizard_map.models import Workspace
from lizard_map.models import WorkspaceItem

from lizard_rainapp.models import GeoObject

logger = logging.getLogger(__name__)

def load_shapefile():
    shapefile_filename = resource_filename('lizard_rainapp',
                                           'shape/gemeenten2009.shp')
    # original_srs = ogr.osr.SpatialReference()
    # original_srs.ImportFromProj4(coordinates.RD)
    # target_srs = ogr.osr.SpatialReference()
    # target_srs.ImportFromEPSG(4326)
    # coordinate_transformation = ogr.osr.CoordinateTransformation(original_srs, target_srs)

    drv = ogr.GetDriverByName('ESRI Shapefile')
    source = drv.Open(shapefile_filename)
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

        kwargs = {
            'municipality_id': feature.GetField(feature.GetFieldIndex('ID')),
            'name': feature.GetField(feature.GetFieldIndex('NAME')),
            'code': feature.GetField(feature.GetFieldIndex('GEM_CODE')),
            'x': feature.GetField(feature.GetFieldIndex('X')),
            'y': feature.GetField(feature.GetFieldIndex('Y')),
            'area': feature.GetField(feature.GetFieldIndex('OPP')),
            'geometry': GEOSGeometry(geom.ExportToWkt(), srid=4326),
        }
        geoobject = GeoObject(**kwargs)
        geoobject.save()
        number_of_features += 1
    logger.info("Added %s municipalty polygons.", number_of_features)


class Command(BaseCommand):
    args = ""
    help = "TODO"

    def handle(self, *args, **options):
        load_shapefile()
