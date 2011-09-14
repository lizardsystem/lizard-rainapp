# -*- coding: utf-8 -*-
# Copyright 2011 Nelen & Schuurmans
from __future__ import division

from django.core.management.base import BaseCommand

from lizard_fewsjdbc.models import JdbcSource
from lizard_rainapp.models import GeoObject
from lizard_rainapp.models import RainValue

import datetime
import logging

logger = logging.getLogger(__name__)

# The offset to add to get_timeseries dates to get the right dates back.
FEWS_OFFSET = datetime.timedelta(hours=-2)
INVESTIGATED_LOCATION = 'GEM_001'
LOOK_BACK_PERIOD = {
    'P.radar.5m':datetime.timedelta(hours=6),
    'P.radar.1h':datetime.timedelta(hours=6),
    'P.radar.3h':datetime.timedelta(hours=6),
    'P.radar.24h':datetime.timedelta(hours=48),
}
REPORT_GROUP_SIZE = 50

class NoDataError(Exception):
    pass

def import_recent_data(datetime_ref):
    """Copy the rainvalues most recent to datetime_ref into local db."""
    js = JdbcSource.objects.get(slug='rainapp')
    fid = 'gemeentes'

    logger.info('Getting parameters from fews and locations from django.')
    pids = [p['parameterid'] for p in js.get_named_parameters(filter_id=fid)]
    lids = [g.municipality_id for g in GeoObject.objects.all()]

    logger.info('Probing location %s for latest values.' %
                INVESTIGATED_LOCATION)

    ts_kwargs = {
        'filter_id': fid,
        'parameter_id': p,
        'end_date': datetime_ref,
        'location_id': INVESTIGATED_LOCATION
    }

    last_value_date = {}

    # Separate loop for probing so that any error occurs right at the start
    for pid in pids:

        ts_kwargs.update({
            'parameter_id': pid,
            'start_date': datetime_ref - LOOK_BACK_PERIOD[pid],
        })
        timeseries = js.get_timeseries(**ts_kwargs)

        if not timeseries:
            raise NoDataError('No data for parameter %s at location %s.' % (
                              ts_kwargs['parameter_id'],
                              ts_kwargs['location_id']))

        last_value_date[pid] = timeseries[-1]['time']


    for pid in pids:

        logger.info('Syncing data for parameter %s.' % pid)
        unit = js.get_unit(pid)
        ts_kwargs.update({
            'parameter_id': pid,
            'start_date': last_value_date[pid] + FEWS_OFFSET,
            'end_date': last_value_date[pid] + FEWS_OFFSET,
        })
        for i, lid in enumerate(lids):
            ts_kwargs.update({
                'location_id': lid
            })
            data = js.get_timeseries(**ts_kwargs)

            if not data:
                logger.debug('no data for %s' % lid)
                continue

            if len(data) > 1:
                logger.debug('Ambiguous for parameter %s at location %s.' % (
                              ts_kwargs['parameter_id'],
                              ts_kwargs['location_id']))
                logger.debug('length of data: %s' % len(data))
                continue

            rainvalue = {
                'geo_object': GeoObject.objects.get(municipality_id=lid),
                'parameterkey': pid,
                'unit': unit,
                'datetime': data[0]['time'].replace(tzinfo=None),
                'value': data[0]['value'],
            }

            if not RainValue.objects.filter(**rainvalue).exists():
                RainValue(**rainvalue).save()

            if (i + 1) / REPORT_GROUP_SIZE == int((i + 1) / REPORT_GROUP_SIZE):
                logger.info('synced %s values.' % (i + 1))


class Command(BaseCommand):
    args = ""
    help = "TODO"

    def handle(self, *args, **options):
        datetime_ref = datetime.datetime.now()
        import_recent_data(datetime_ref=datetime_ref)
