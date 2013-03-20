from datetime import datetime
from datetime import timedelta
import logging

from django.test import TestCase
import pytz

from lizard_rainapp.calculations import herhalingstijd
from lizard_rainapp.calculations import meter_square_to_km_square
from lizard_rainapp.calculations import moving_sum

logger = logging.getLogger(__name__)

UTC = pytz.timezone('UTC')


def generate_values(dt_start, dt_stop, td_step, unit, value):
    """Generate list of values similar to the one returned by fews."""

    # Make tzaware
    dt_start_utc = UTC.localize(dt_start)
    dt_stop_utc = UTC.localize(dt_stop)

    # Initial conditions
    dt = dt_start_utc
    values = []

    # Loop
    while (dt <= dt_stop_utc):

        values.append({
            'unit': unit,
            'value': value,
            'datetime': dt,
        })
        dt += td_step

    return values


class ComputeTestSuite(TestCase):

    def test_meter_square_to_km_square(self):
        """Test area conversion."""
        self.assertAlmostEqual(5.2,
                               meter_square_to_km_square(5.2 * pow(10, 6)))

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
        start_date = UTC.localize(start_date)
        end_date = UTC.localize(end_date)

        moving_sum_kwargs = {
            'values': generate_values(**generate_values_kwargs),
            'td_window': timedelta(hours=1),
            'td_value': td_step,
            'start_date_utc': start_date,
            'end_date_utc': end_date}

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
