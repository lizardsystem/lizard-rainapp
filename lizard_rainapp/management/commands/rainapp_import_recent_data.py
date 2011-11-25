# -*- coding: utf-8 -*-
# Copyright 2011 Nelen & Schuurmans
from __future__ import division

from django.conf import settings
from django.core.management.base import BaseCommand

from lizard_fewsjdbc.models import JdbcSource
from lizard_rainapp.models import GeoObject
from lizard_rainapp.models import RainValue
from lizard_rainapp.models import CompleteRainValue

import datetime
import logging
import sys

logger = logging.getLogger(__name__)

# The offset to add to get_timeseries dates to get the right dates back.
# ^^^ Update: As of 2011-09-16, there is no offset anymore, so it can be set
# to zero, and after some months removed.
INVESTIGATED_LOCATION = getattr(settings, 'RAINAPP_IMPORT_START_LOCATION', 'GEM_001')

LOOK_BACK_PERIOD = {
    'P.radar.5m': datetime.timedelta(hours=6),
    'P.radar.1h': datetime.timedelta(hours=6),
    'P.radar.3h': datetime.timedelta(hours=6),
    'P.radar.24h': datetime.timedelta(hours=48),
}
REPORT_GROUP_SIZE = 50


class NoDataError(Exception):
    pass


def import_recent_data(datetime_ref):
    """Copy the rainvalues most recent to datetime_ref into local db."""
    js = JdbcSource.objects.get(slug='rainapp')
    fid = getattr(settings,'RAINAPP_FILTER', 'gemeentes')

    logger.info('Getting parameters from fews and locations from django.')
    pids = [p['parameterid'] for p in js.get_named_parameters(filter_id=fid)]
    lids = [g.municipality_id for g in GeoObject.objects.all()]

    logger.info('Probing location %s for latest values.' %
                INVESTIGATED_LOCATION)

    ts_kwargs = {
        'filter_id': fid,
        'parameter_id': None,
        'end_date': datetime_ref,
        'location_id': INVESTIGATED_LOCATION,
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

        last_value_date[pid] = timeseries[-1]['time'].replace(tzinfo=None)

    for pid in pids:
        print 'pid='+pid

        unit = js.get_unit(pid)
        ts_kwargs.update({
            'parameter_id': pid,
            'start_date': last_value_date[pid],
            'end_date': last_value_date[pid],
        })

        completerainvalue = {
            'parameterkey': pid,
            'datetime': last_value_date[pid],
        }
        
        # Only do the import if it hasn't been done yet
        if not CompleteRainValue.objects.filter(**completerainvalue).exists():
            logger.info('Syncing data for parameter %s.' % pid)
            for i, lid in enumerate(lids):
                ts_kwargs.update({
                    'location_id': lid,
                })

                try:
                    data = js.get_timeseries(**ts_kwargs)
                except:
                    error_type = sys.exc_info()[0]
                    info_str = ('Error getting timeseries for %s. The error ' +
                                    'was %s; putting -2.') % (lid, error_type)
                    logger.info(info_str)
                    data = [{'time': last_value_date[pid], 'value': -2}]

                if not data:
                    logger.info('no data for %s, putting -1.' % lid)
                    data = [{'time': last_value_date[pid], 'value': -1}]

                if len(data) > 1:
                    info_str = ('Ambiguous data for parameter %s at location ' +
                                   '%s. Putting -3.') % (pid, lid)
                    logger.info(info_str)
                    data = [{'time': last_value_date[pid], 'value': -3}]

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

            # After all data is received, a completerainvalueobject is stored, to
            # indicate to other code that the rainvalues for this datetime can be
            # used.
            CompleteRainValue(**completerainvalue).save()


def delete_older_data(datetime_threshold):
    """Delete any data older than datetime_threshold."""

    outdated_rvs = RainValue.objects.filter(datetime__lt=datetime_threshold)
    logger.info('Deleting %s old rainvalue objects.' % outdated_rvs.count())
    outdated_rvs.delete()
    CompleteRainValue.objects.filter(datetime__lt=datetime_threshold).delete()


class Command(BaseCommand):
    args = ""
    help = "TODO"

    def handle(self, *args, **options):

        now = datetime.datetime.now()

        datetime_threshold = now - datetime.timedelta(days=3)
        delete_older_data(datetime_threshold=datetime_threshold)

        import_recent_data(datetime_ref=now)

