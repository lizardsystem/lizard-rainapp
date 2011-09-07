from datetime import timedelta
from datetime import datetime
from datetime import tzinfo

from django.test import TestCase
from lizard_rainapp.calculations import herhalingstijd
from lizard_rainapp.calculations import moving_sum

import logging
logger = logging.getLogger(__name__)

ZERO = timedelta(0)
TZ_OFFSET = 60
TZ_NAME = 'Test'


def generate_values(dt_start, dt_stop, td_step, unit, value):
    """Generate list of values similar to the one returned by fews."""
    timezone_info = FixedOffset(TZ_OFFSET, TZ_NAME)

    # Make tzaware
    dt_start_tz = dt_start.replace(tzinfo=timezone_info)
    dt_stop_tz = dt_stop.replace(tzinfo=timezone_info)

    # Initial conditions
    dt = dt_start_tz
    values = []

    # Loop
    while (dt <= dt_stop_tz):

        values.append({
            'unit': unit,
            'value': value,
            'datetime': dt,
        })
        dt += td_step

    return values


class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC.

    From http://docs.python.org/library/datetime.html

    A class building tzinfo objects for fixed-offset time zones.
    Note that FixedOffset(0, "UTC") is a different way to build a
    UTC tzinfo object."""
    def __init__(self, offset, name):
        self.__offset = timedelta(minutes=offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return ZERO


class ComputeTestSuite(TestCase):

    def test_herhalingstijd(self):
        """Test herhalingstijd calculation."""
        self.assertAlmostEqual(25, herhalingstijd(bui_duur=24,
                                                  oppervlak=50,
                                                  neerslag_som=62.82))

    def test_moving_sum(self):
        """Test moving_sum calculation."""
        start_date = datetime(year=2011, month=9, day=6)
        end_date = datetime(year=2011, month=9, day=8)

        td_step = timedelta(hours=24)

        generate_values_kwargs = {'dt_start': start_date,
                                  'dt_stop': end_date,
                                  'td_step': td_step,
                                  'unit': 'AnyUnit',
                                  'value': 1}

        # Make start_date and end_date tz aware, just as in rain_stats from
        # adapter
        timezone_info = FixedOffset(TZ_OFFSET, TZ_NAME)
        start_date = start_date.replace(tzinfo=timezone_info)
        end_date = end_date.replace(tzinfo=timezone_info)

        moving_sum_kwargs = {
            'values': generate_values(**generate_values_kwargs),
            'td_window': timedelta(hours=1),
            'td_value': td_step,
            'start_date': start_date,
            'end_date': end_date}

        # 24 hour data and a 1 hour window, there should be no max_values
        self.assertEqual(len(moving_sum(**moving_sum_kwargs)), 0)

        # 3 values of 24 hour data and a 24 hour window, there will be 3
        # max_values of 1 each
        moving_sum_kwargs['td_window'] = timedelta(days=1)
        self.assertEqual(len(moving_sum(**moving_sum_kwargs)), 3)

        # if there are more values before and after the window, they are
        # neglected.
        generate_values_kwargs['dt_start'] -= timedelta(days=2)
        generate_values_kwargs['dt_stop'] += timedelta(days=2)
        moving_sum_kwargs['values'] = generate_values(**generate_values_kwargs)
        self.assertEqual(len(moving_sum(**moving_sum_kwargs)), 3)

        # if the values are offset compared to the daterange by
        # some hours, only 2 values fit within the daterange that is
        # exactly two calendar days.
        generate_values_kwargs['dt_start'] -= timedelta(hours=7)
        generate_values_kwargs['dt_stop'] += timedelta(hours=7)
        moving_sum_kwargs['values'] = generate_values(**generate_values_kwargs)
        self.assertEqual(len(moving_sum(**moving_sum_kwargs)), 2)

        # A 48 hour window should reveal at least the maximum of 2,
        # which is the sum of two 24 hour values of 1
        moving_sum_kwargs['td_window'] = timedelta(days=2)
        ms = moving_sum(**moving_sum_kwargs)
        sums = [m['value'] for m in ms]
        self.assertEqual(max(sums), 2)
