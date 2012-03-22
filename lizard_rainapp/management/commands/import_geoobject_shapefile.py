# -*- coding: utf-8 -*-
# Copyright 2011 Nelen & Schuurmans
import logging
import ConfigParser
import os

from pkg_resources import resource_filename

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from osgeo import ogr

from lizard_rainapp.models import GeoObject
from lizard_rainapp.models import RainappConfig

logger = logging.getLogger(__name__)


def load_shapefiles(config_file, loader):
    """
    For each section in the config file, read in the information, put
    in defaults or raise error messages in case of missing settings,
    then call the loader.

    The 'shapefile' path in the config file must always be relative to
    the cfg file, this function turns it into an absolute path.

    The loader is given as an argument for easy testability."""
    cp = ConfigParser.ConfigParser()
    cp.readfp(open(config_file))

    for section in cp.sections():
        options = dict(cp.items(section))

        if 'shapefile' not in options:
            raise ValueError('Missing shapefile option in section %s'
                             % section)

        options['shapefile'] = os.path.join(os.path.dirname(config_file),
                                            options['shapefile'])
        loader(section, options)


def load_shapefile(section, options):
    if 'shapefile' in options:
        drv = ogr.GetDriverByName('ESRI Shapefile')
        source = drv.Open(options['shapefile'])
    else:
        source = None

    if source is None:
        raise ValueError("Shapefile (%s) not found." %
                         (options.get('shapefile', "None"),))

    if 'slug' in options:
        try:
            rainapp_config = RainappConfig.objects.get(slug=options['slug'])
        except RainappConfig.DoesNotExist:
            raise ValueError("RainappConfig with slug '%s' not found." %
                             (options['slug'],))
    else:
        raise ValueError("No Rainapp Config slug defined.")

    layer = source.GetLayer()

    logger.info("Importing new geoobjects...")
    number_of_features = 0

    for feature in layer:
        geom = feature.GetGeometryRef()

        def get_field(fieldname, default=None):
            try:
                name = options[fieldname]
                return feature.GetField(feature.GetFieldIndex(name))
            except ValueError:
                return default

        kwargs = {
            'municipality_id': get_field('id_field'),
            'name': get_field('name_field'),
            'code': get_field('code_field'),
            'x': get_field('x_field'),
            'y': get_field('y_field'),
            'area': get_field('area_field', -1),
            'geometry': GEOSGeometry(geom.ExportToWkt(), srid=4326),
            'config': rainapp_config,
        }

        geoobject = GeoObject(**kwargs)
        geoobject.save()
        number_of_features += 1
    logger.info("Added %s polygons.", number_of_features)
    return number_of_features


def clear_old_data():
    if GeoObject.objects.count():
        logger.info("First deleting the existing geoobjects...")
        GeoObject.objects.all().delete()


class Command(BaseCommand):
    args = ""
    help = "TODO"

    def handle(self, *args, **options):
        config_file = getattr(settings, 'RAINAPP_CONFIGFILE',
                              resource_filename('lizard_rainapp',
                                                'shape/gemeenten2009.cfg'))
        logger.info("Using config file %s." % (config_file,))
        clear_old_data()
        load_shapefiles(config_file, load_shapefile)
