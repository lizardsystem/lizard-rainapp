import os
from django.test import TestCase
from pkg_resources import resource_filename

from django.contrib.gis.geos import GEOSGeometry

from lizard_rainapp.management.commands import import_geoobject_shapefile
import_geoobject_shapefile  # Pyflakes
from import_geoobject_shapefile import load_shapefile
from import_geoobject_shapefile import load_shapefiles
from import_geoobject_shapefile import clear_old_data

from lizard_rainapp.models import GeoObject
from lizard_rainapp.models import RainappConfig


SOME_GEOOBJECT = 'POINT (30 10)'


class TestImportShapefiles(TestCase):
    def test_load_shapefiles_nonexisting(self):
        # Nonexisting file: IOError
        def unexisting_file():
            load_shapefiles("wheeee", None)
        self.assertRaises(IOError, unexisting_file)

    def test_load_shapefiles_missing_option(self):
        # Various missing or wrong options: ValueError
        def dummy_file():
            testdummyconfig = resource_filename('lizard_rainapp',
                                                'testshapes/testdummy.cfg')
            load_shapefiles(testdummyconfig, None)
        self.assertRaises(ValueError, dummy_file)

    def test_load_shapefiles_call_loader(self):
        # Load a sample config file and call loader
        def loader(section, options, testobject=self):
            testobject.assertTrue(os.path.exists(options['shapefile']))

            if section == 'Afvoervlakken':
                testobject.assertEquals(options['thisisatest'], 'whee')
            elif section == 'AlmereGebieden':
                testobject.assertEquals(options['thisisatest'], 'boo')

        testconfig = resource_filename('lizard_rainapp',
                                       'testshapes/testshapes.cfg')
        load_shapefiles(testconfig, loader)

    def test_clear_data(self):
        config = RainappConfig(name="test", jdbcsource_id=0,
                               filter_id="test", slug="test")
        config.save()

        geo = GeoObject(name="test", x=0, y=0, area=0,
                        geometry=GEOSGeometry(SOME_GEOOBJECT),
                        config=config)
        count = GeoObject.objects.count()
        geo.save()
        self.assertEqual(GeoObject.objects.count(), count + 1)
        clear_old_data()
        self.assertEqual(GeoObject.objects.count(), 0)

    def test_loader(self):
        RainappConfig(name="test", jdbcsource_id=0,
                      filter_id="test", slug="test").save()
        options = {
            'shapefile': resource_filename('lizard_rainapp',
                                           'shape/gemeenten2009.shp'),
            'id_field': 'ID',
            'name_field': 'NAME',
            'code_field': 'GEM_CODE',
            'x_field': 'X',
            'y_field': 'Y',
            'area_field': 'OPP',
            'slug': 'test',
        }

        def unexisting_filename():
            o = options.copy()
            o.update({'shapefile': 'wheeeeeeeeeeeeeeeeeeeeeeeeeee.xxx'})
            load_shapefile('section', o)
        self.assertRaises(ValueError, unexisting_filename)

        count = load_shapefile('section', options)
        self.assertEqual(GeoObject.objects.count(), count)
        self.assertEqual(452, count)
