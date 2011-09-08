# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
# from django.db import models

# Create your models here.
import logging

from django.contrib.gis.db import models

logger = logging.getLogger(__name__)

class MunicipalityPolygon(models.Model):
    """Line elements from river shapefile."""
    municipality_id = models.CharField(max_length=16)
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=16, null=True)
    x = models.FloatField()
    y = models.FloatField()
    area = models.FloatField() # In square meters
    geom = models.GeometryField(srid=4326)
    objects = models.GeoManager()

