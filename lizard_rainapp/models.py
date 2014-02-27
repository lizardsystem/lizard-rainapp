# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
import logging

from django.core.urlresolvers import reverse
from django.contrib.gis.db import models

from lizard_fewsjdbc.models import JdbcSource
from lizard_map.models import Setting as MapSetting

logger = logging.getLogger(__name__)


class RainappConfig(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)

    jdbcsource = models.ForeignKey(JdbcSource)
    filter_id = models.CharField(max_length=128)

    def __unicode__(self):
        return (u'%s (%s in %s)' %
                (self.name, self.filter_id, self.jdbcsource.name))

    @property
    def has_geoobjects(self):
        return GeoObject.objects.filter(
            config=self).exists()

    def shape_download_url(self):
        return reverse('lizard_rainapp_download_shape', kwargs=dict(
                slug=self.slug))

    @classmethod
    def get_by_jdbcslug_and_filter(cls, jdbc_slug, filter_id):
        try:
            jdbcsource = JdbcSource.objects.get(slug=jdbc_slug)
        except JdbcSource.DoesNotExist:
            raise ValueError("JdbcSource with slug '%s' not found." %
                             jdbc_slug)

        try:
            return cls.objects.get(jdbcsource=jdbcsource, filter_id=filter_id)
        except cls.DoesNotExist:
            raise ValueError("RainappConfig filter_id '%s' not found." %
                             filter_id)


class GeoObject(models.Model):
    """Line elements from river shapefile."""

    municipality_id = models.CharField(max_length=16)
    name = models.CharField(max_length=128)

    x = models.FloatField()
    y = models.FloatField()

    config = models.ForeignKey(RainappConfig)

    area = models.FloatField()  # In square meters
    geometry = models.GeometryField(srid=4326)
    objects = models.GeoManager()

    def __unicode__(self):
        return self.name


class RainValue(models.Model):
    """RainData stored locally. datetime is copied from fews datetime."""
    geo_object = models.ForeignKey('GeoObject')

    config = models.ForeignKey(RainappConfig)

    parameterkey = models.CharField(max_length=32)

    unit = models.CharField(max_length=32)
    datetime = models.DateTimeField()
    value = models.FloatField()


class CompleteRainValue(models.Model):
    """Date and parameter for which a complete set of RainValues
    has been stored. Again, datetime is copied from fews datetime."""
    config = models.ForeignKey(RainappConfig)

    parameterkey = models.CharField(max_length=32)
    datetime = models.DateTimeField()


class Setting(MapSetting):
    """Settings like present in lizard-map, but use a different CACHE_KEY."""
    CACHE_KEY = 'lizard-rainapp.Setting'
