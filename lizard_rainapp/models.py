# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# from django.db import models

# Create your models here.
import logging

from django.contrib.gis.db import models
from lizard_map.models import Setting as MapSetting

logger = logging.getLogger(__name__)


class GeoObject(models.Model):
    """Line elements from river shapefile."""
    municipality_id = models.CharField(max_length=16)
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=16, null=True)
    x = models.FloatField()
    y = models.FloatField()

    # Field appears to be unused? -RemcoG 2011 11 25
    area = models.FloatField()  # In square meters
    geometry = models.GeometryField(srid=4326)
    objects = models.GeoManager()

    def __unicode__(self):
        return self.name


class RainValue(models.Model):
    """RainData stored locally. datetime is copied from fews datetime."""
    geo_object = models.ForeignKey('GeoObject')
    parameterkey = models.CharField(max_length=32)
    unit = models.CharField(max_length=32)
    datetime = models.DateTimeField()
    value = models.FloatField()


class CompleteRainValue(models.Model):
    """Date and parameter for which a complete set of RainValues
    has been stored. Again, datetime is copied from fews datetime."""
    parameterkey = models.CharField(max_length=32)
    datetime = models.DateTimeField()

class Setting(MapSetting):
    """Settings like present in lizard-map, but use a different CACHE_KEY."""
    CACHE_KEY = 'lizard-rainapp.Setting'
