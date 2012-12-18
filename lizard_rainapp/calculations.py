# -*- coding: utf-8 -*-
from __future__ import division
from math import log, exp

import datetime
import pytz

from django.conf import settings

import logging
logger = logging.getLogger(__name__)

B_loc_1 = 17.9189977
B_loc_2 = 0.2245493
B_loc_3 = -3.5714538
B_loc_4 = 0.4264825
B_loc_5 = 0.1281047

B_shp_1 = -0.20559396
B_shp_2 = 0.01767472

B_disp_1 = 0.33739862
B_disp_2 = -0.01768042
B_disp_3 = -0.01398795


UNIT_TO_TIMEDELTA = {
    'mm/24hr': datetime.timedelta(hours=24),
    'mm/24h': datetime.timedelta(hours=24),
    'mm/3hr': datetime.timedelta(hours=3),  # Not encountered yet
    'mm/3h': datetime.timedelta(hours=3),  # Not encountered yet
    'mm/hr': datetime.timedelta(hours=1),
    'mm/h': datetime.timedelta(hours=1),
    'mm/5min': datetime.timedelta(minutes=5),
}


def t_to_string(t):
    if t is None:
        return '-'
    elif t > 1:
        return 'T = %i' % t
    else:
        return 'T ≤ 1'


def rain_stats(values,
               area_km2,
               td_window,
               start_date_utc,
               end_date_utc):
    """Calculate stats.

    Expects utc, returns site timezone datetimes... Sorry."""

    logger.debug(('Calculating rain stats for' +
                  'start=%s, end=%s, td_window=%s') %
                 (start_date_utc, end_date_utc, td_window))

    if not values:
        return {
            'td_window': td_window,
            'max': None,
            'start': None,
            'end': None,
            't': t_to_string(None)}

    tz = pytz.timezone(settings.TIME_ZONE)

    td_value = UNIT_TO_TIMEDELTA[values[0]['unit']]
    max_values = moving_sum(values,
                            td_window,
                            td_value,
                            start_date_utc,
                            end_date_utc)

    if max_values:
        max_value = max(max_values, key=lambda i: i['value'])

        hours = td_window.days * 24 + td_window.seconds / 3600.0
        t = herhalingstijd(hours, area_km2, max_value['value'])
    else:
        max_value = {'value': None,
                     'datetime_start_utc': None,
                     'datetime_end_utc': None}
        t = None

    if max_value['datetime_start_utc'] is not None:
        datetime_start_site_tz = max_value[
            'datetime_start_utc'].astimezone(tz)
    else:
        datetime_start_site_tz = None
    if max_value['datetime_end_utc'] is not None:
        datetime_end_site_tz = max_value[
            'datetime_end_utc'].astimezone(tz)
    else:
        datetime_end_site_tz = None

    return {
        'td_window': td_window,
        'max': max_value['value'],
        'start': datetime_start_site_tz,
        'end': datetime_end_site_tz,
        't': t_to_string(t)}


def meter_square_to_km_square(meter_square):
    return meter_square / pow(10, 6)


def herhalingstijd(bui_duur, oppervlak, neerslag_som):
    """Calculate 'herhalingstijd' of a rainshower.

    bui_duur in [uren]
    oppervlak in [vierkante km]
    neerslag_som in [mm]
    """
    #locatie parameter (formule 6 Aart)
    loc = B_loc_1 * bui_duur ** B_loc_2 + (
        B_loc_3 + B_loc_4 * log(bui_duur)) * oppervlak ** B_loc_5
    #vorm parameter (formule 8 Aart)
    vorm = B_shp_1 + B_shp_2 * log(oppervlak)
    #dispersie/schaal parameter (formule 7 Aart)
    disp = B_disp_1 + B_disp_2 * log(bui_duur) + B_disp_3 * log(oppervlak)

    #afgeleide schaal parameter:
    schaal = disp * loc

    #herhalingstijd
    return round(1 / (1 - (exp(
        -(1 - (neerslag_som - loc) * (vorm / schaal)) ** (1 / vorm)))), 0)


def moving_sum(values, td_window, td_value, start_date_utc, end_date_utc):
    """Return list of summed values in window of td_window.

    Requires len(values) > 0."""
    max_values = []

    # End_date often ends with 23:59:59, we want to include at
    # least 1 day in case td_window=1 day, thus the 2 seconds.
    window_start_last = (end_date_utc - td_window +
                         datetime.timedelta(seconds=2))

    # Calculate start of first window based on td_value. The whole timespan to
    # which the first value which hypothetically could be as the start_date
    # minus the td_value, should be in the window.
    # window_increment is also based on td_value
    if (td_value.days == 1):
        # 24 hour data, fix to hour and subtract td_value
        window_start = start_date_utc.replace(hour=0,
                                              minute=0,
                                              second=0,
                                              microsecond=0) - td_value
        # It is not known in advance at which hour of day the 24 hour data
        # is stored, so the window advances by hour and not by 24 hours
        window_increment = datetime.timedelta(hours=1)
    elif (td_value.seconds == 3600):
        window_increment = td_value
        # 1 hour data, fix to hour and subtract td_value
        window_start = start_date_utc.replace(hour=0,
                                              minute=0,
                                              second=0,
                                              microsecond=0) - td_value
    elif (td_value.seconds == 300):
        window_increment = td_value
        # 5 minute data, fix to whole five minutes before startdate
        window_start = start_date_utc.replace(hour=0,
                                              minute=5 * int(
                                                start_date_utc.minute / 5),
                                              second=0,
                                              microsecond=0) - td_value
    # Fast way to calculate sum values.
    len_values = len(values)
    min_index, max_index = 0, -1  # Nothing todo with backwards indexing...
    sum_values = 0

    while window_start < window_start_last:
        window_end = window_start + td_window

        # Calculate value by subtracting value(s) from front and
        # adding new value(s) from end. Min_index and max_index
        # always represent the current contents of sum_values.

        # Skip values that are not in the start of the window.
        while (max_index + 1 < len_values and
               values[max_index + 1]['datetime'] - td_value <
                             window_start):
            min_index += 1
            max_index += 1

        # For a value to be added to the sum both ends of the timespan to
        # which the value applies need to be in the window.
        while (max_index + 1 < len_values and
               values[max_index + 1]['datetime'] - td_value >=
                             window_start and
               values[max_index + 1]['datetime'] <= window_end):

            max_index += 1
            sum_values += values[max_index]['value']

        # For a value to be removed only the oldest end of the timespan to
        # which the value applies needs to fall outside the window, since
        # the window is moving forward in time.
        while (min_index <= max_index and
               values[min_index]['datetime'] - td_value < window_start):
            sum_values -= values[min_index]['value']
            min_index += 1

        if max_index >= min_index:
            max_values.append({
                    'value': sum_values,
                    'datetime_start_utc': window_start,
                    'datetime_end_utc': window_end,
            })

        window_start += window_increment
    return max_values
