from __future__ import division
import datetime
import logging
import iso8601

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils import simplejson as json

from lizard_fewsjdbc.layers import FewsJdbc
from lizard_map.daterange import current_start_end_dates
from lizard_rainapp.calculations import herhalingstijd
from lizard_rainapp.calculations import moving_sum

from nens_graph.rainapp import RainappGraph

logger = logging.getLogger(__name__)

UNIT_TO_TIMEDELTA = {
    'mm/24hr': datetime.timedelta(hours=24),
    'mm/3hr': datetime.timedelta(hours=3),  # Not encountered yet
    'mm/hr': datetime.timedelta(hours=1),
    'mm/5min': datetime.timedelta(minutes=5),
}


class RainAppAdapter(FewsJdbc):
    """
    Adapter for Rain app.

    identifier: {'location': <locationid>}
    """

    def _get_location_name(self, identifier):
        """Return location_name for identifier."""
        named_locations = self._locations()
        location_id = identifier['location']
        location_name = [
            location['location'] for location in named_locations
            if location['locationid'] == location_id][0]

        return location_name

    def image(self,
              identifiers,
              start_date,
              end_date,
              width,
              height,
              layout_extra=None):
        """Return png image data for barchart."""
        today = datetime.datetime.now()
        graph = RainappGraph(start_date, end_date,
                      width=width, height=height, today=today)
        # Gets timeseries, draws the bars, sets  the legend
        for identifier in identifiers:
            location_name = self._get_location_name(identifier)
            cached_value_result = self._cached_values(identifier,
                                                      start_date,
                                                      end_date)
            dates_notz = [row['datetime'].replace(tzinfo=None)
                          for row in cached_value_result]

            values = [row['value'] for row in cached_value_result]
            units = [row['unit'] for row in cached_value_result]
            unit = ''
            if len(units) > 0:
                unit = units[0]
            if values:
                unit_timedelta = UNIT_TO_TIMEDELTA.get(unit, None)
                if unit_timedelta:
                    # We can draw bars corresponding to period
                    bar_width = graph.get_bar_width(unit_timedelta)
                    offset = -1 * unit_timedelta
                    offset_dates = [d + offset for d in dates_notz]
                else:
                    # We can only draw spikes.
                    bar_width = 0
                    offset_dates = dates_notz
                graph.axes.bar(offset_dates,
                               values,
                               edgecolor='blue',
                               width=bar_width,
                               label=location_name)
            graph.set_ylabel(unit)
            # graph.legend()
            graph.suptitle(location_name)

            # Use first identifier and breaks the loop
            break

        graph.responseobject = HttpResponse(content_type='image/png')

        return graph.png_response()

    def _cached_values(self, identifier, start_date, end_date):
        """
        Same as self.values, but cached.

        The stored values are rounded in days, a 'little bit
        more'. Else the cache will always miss.
        """
        start_date_cache = datetime.datetime(
            start_date.year, start_date.month, start_date.day)
        end_date_cache = (
            datetime.datetime(
                end_date.year, end_date.month, end_date.day) +
                datetime.timedelta(days=1))

        cache_key = hash('%s::%s::%s::%s::%s::%s' % (
                self.jdbc_source.id, self.filterkey, self.parameterkey,
                identifier['location'], start_date_cache, end_date_cache))
        # Datetimes are in string and stored in datetime_str.
        logger.debug('Trying cache...')
        values = cache.get(cache_key)
        if values is None:
            logger.debug('Caching values for %s' % identifier['location'])
            values = self.values(identifier, start_date, end_date)
            # Convert datetimes to strings, the
            # iso8601.iso8601.FixedOffset will not de-pickle.
            for value in values:
                value['datetime_str'] = value['datetime'].isoformat()
                del value['datetime']
            cache.set(cache_key, values, 5 * 60)
            logger.debug('Cache written')
        else:
            logger.debug('Got timeseries from cache')

        if not values:
            return []

        # Convert datetime strings to datetime in values
        for value in values:
            value['datetime'] = iso8601.parse_date(value['datetime_str'])
            del value['datetime_str']

        # Make start_date and end_date tz aware
        start_date = start_date.replace(tzinfo=values[0]['datetime'].tzinfo)
        end_date = end_date.replace(tzinfo=values[0]['datetime'].tzinfo)

        # Remove datetimes out of range.
        while values and values[0]['datetime'] < start_date:
            del values[0]
        while values and values[-1]['datetime'] > end_date:
            del values[-1]

        return values

    def rain_stats(self, values, td_window, start_date, end_date):
        """
        Calculate stats.

        """
        logger.debug(('Calculating rain stats for' +
                      'start=%s, end=%s, td_window=%s') %
                     (start_date, end_date, td_window))
        if not values:
            return {
                'td_window': td_window,
                'max': None,
                'start': None,
                'end': None,
                't': None}

        # Make start_date and end_date tz aware
        start_date = start_date.replace(tzinfo=values[0]['datetime'].tzinfo)
        end_date = end_date.replace(tzinfo=values[0]['datetime'].tzinfo)

        td_value = UNIT_TO_TIMEDELTA[values[0]['unit']]
        max_values = moving_sum(values,
                                td_window,
                                td_value,
                                start_date,
                                end_date)

        if max_values:
            max_value = max(max_values, key=lambda i: i['value'])
            max_value['datetime_end'] = max_value['datetime'] + td_window
            hours = td_window.days * 24 + td_window.seconds / 3600.0
            t = herhalingstijd(hours, 25, max_value['value'])
        else:
            max_value = {'value': None, 'datetime': None, 'datetime_end': None}
            t = None

        return {
            'td_window': td_window,
            'max': max_value['value'],
            'start': max_value['datetime'],
            'end': max_value['datetime_end'],
            't': t}

    def html(self, snippet_group=None, identifiers=None, layout_options=None):
        """
        Popup with graph - table - bargraph.
        """
        add_snippet = layout_options.get('add_snippet', False)
        if snippet_group:
            identifiers = [
                snippet.identifier
                for snippet in snippet_group.snippets.filter(visible=True)]
        title = 'RainApp (%s)' % ', '.join(
            [self._get_location_name(identifier)
             for identifier in identifiers])

        # Make table with given identifiers.
        # Layer options contain request - not the best way but it works.
        start_date, end_date = current_start_end_dates(
            layout_options['request'])

        td_windows = [datetime.timedelta(days=2),
                      datetime.timedelta(days=1),
                      datetime.timedelta(hours=3),
                      datetime.timedelta(hours=1)]

        info = []

        symbol_url = self.symbol_url()
        if snippet_group:
            # Note that the rainapp image does not support tweaking labels
            image_url_base = reverse(
                "lizard_map.snippet_group_image",
                kwargs={'snippet_group_id': snippet_group.id},
            )
        else:
            image_url_base = reverse(
                "lizard_map.workspace_item_image",
                kwargs={'workspace_item_id': self.workspace_item.id},
            )

        for identifier in identifiers:

            values = self._cached_values(identifier, start_date, end_date)

            if snippet_group:
                url_extra = ''
            else:
                identifier_escaped = json.dumps(identifier).replace('"', '%22')
                url_extra = '?&identifier=%s' % identifier_escaped

            info.append({
                'identifier': identifier,
                'shortname': '%s - %s' % (
                    self._get_location_name(identifier),
                    self.workspace_item.name),
                'name': '%s - %s' % (
                    self._get_location_name(identifier),
                    self.workspace_item.name),
                'location': self._get_location_name(identifier),
                'table': [self.rain_stats(values,
                                          td_window,
                                          start_date,
                                          end_date)
                          for td_window in td_windows],
                'image_url': image_url_base + url_extra,
            })

        return render_to_string(
            'lizard_rainapp/popup_rainapp.html',
            {'title': title,
             'symbol_url': symbol_url,
             'add_snippet': add_snippet,
             'workspace_item': self.workspace_item,
             'info': info})
