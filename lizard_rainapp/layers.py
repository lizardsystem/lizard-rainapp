# -*- coding: utf-8 -*-
from __future__ import division
import datetime
import locale
import logging
import iso8601
import mapnik
import pytz

from django.db.models import Max
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils import simplejson as json
from django.contrib.gis.geos import Point

from lizard_fewsjdbc.layers import FewsJdbc
from lizard_map.daterange import current_start_end_dates
from lizard_map.coordinates import RD
from lizard_map.coordinates import google_to_rd
from lizard_shape.models import ShapeLegendClass
from lizard_rainapp.calculations import herhalingstijd
from lizard_rainapp.calculations import moving_sum
from lizard_rainapp.calculations import meter_square_to_km_square
from lizard_rainapp.models import GeoObject
from lizard_rainapp.models import CompleteRainValue

from nens_graph.rainapp import RainappGraph

logger = logging.getLogger(__name__)

# Requires correct locale be generated on the server.
# On ubuntu: check with locale -a
# On ubuntu: sudo locale-gen nl_NL.utf8
try:
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF8')
except locale.Error:
    logger.debug('No locale nl_NL.UTF8 on this os. Using default locale.')

UNIT_TO_TIMEDELTA = {
    'mm/24hr': datetime.timedelta(hours=24),
    'mm/3hr': datetime.timedelta(hours=3),  # Not encountered yet
    'mm/hr': datetime.timedelta(hours=1),
    'mm/5min': datetime.timedelta(minutes=5),
}

LEGEND_DESCRIPTOR = 'Rainapp'
UTC = pytz.timezone('UTC')


class RainAppAdapter(FewsJdbc):
    """
    Adapter for Rain app.

    identifier: {'location': <locationid>}
    """
    def __init__(self, *args, **kwargs):
        super(RainAppAdapter, self).__init__(
            *args, **kwargs)

        self.tz = pytz.timezone(settings.TIME_ZONE)

    def _to_utc(self, *datetimes):
        """Convert datetimes to UTC."""
        datetimes_utc = []

        for d in datetimes:
            if d.tzinfo is None:
                datetimes_utc.append(self.tz.localize(d).astimezone(UTC))
            else:
                datetimes_utc.append(d.astimezone(UTC))

        if len(datetimes) > 1:
            return datetimes_utc
        return datetimes_utc[0]

    def _t_to_string(self, t):
        logger.debug(t)
        if t is None:
            return '-'
        elif t > 1:
            return 'T = %i' % t
        else:
            return 'T ≤ 1'

    def _get_location_name(self, identifier):
        """Return location_name for identifier."""
        named_locations = self._locations()
        location_id = identifier['location']
        location_name = [
            location['location'] for location in named_locations
            if location['locationid'] == location_id][0]

        return location_name

    def layer(self, *args, **kwargs):
        """Return mapnik layers and styles."""

        # rainapp_rule = mapnik.Rule()
        # rainapp_rule.set_else(True)
        # rainapp_rule.filter = mapnik.Filter("[value] > 0 and [value] < 0.2")
        # TODO use the legend class and use the layers from the legend.
        # fill = mapnik.PolygonSymbolizer(mapnik.Color('#7F7FFF'))
        # edge = mapnik.LineSymbolizer(mapnik.Color('#0000FF'), 1)
        # rainapp_rule.symbols.extend([fill, edge])

        slc = ShapeLegendClass.objects.get(descriptor=LEGEND_DESCRIPTOR)
        rainapp_style = slc.mapnik_style()
        self.maxdate = CompleteRainValue.objects.filter(
            parameterkey=self.parameterkey).aggregate(
            md=Max('datetime'))['md']

        if self.maxdate is None:
            # Color all shapes according to value -1
            query = """(
                select
                    -1 as value,
                    gob.geometry as geometry
                from
                    lizard_rainapp_geoobject gob
            ) as data"""
        else:
            maxdate_str = self.maxdate.strftime('%Y-%m-%d %H:%M:%S+02')
            query = """(
                select
                    rav.value as value,
                    gob.geometry as geometry
                from
                    lizard_rainapp_geoobject gob
                    join lizard_rainapp_rainvalue rav
                    on rav.geo_object_id = gob.id
                where
                    rav.datetime = '%s' and
                    rav.parameterkey = '%s'
            ) as data""" % (maxdate_str, self.parameterkey)

        query = str(query)  # Seems mapnik or postgis don't like unicode?

        default_database = settings.DATABASES['default']
        datasource = mapnik.PostGIS(
            host=default_database['HOST'],
            user=default_database['USER'],
            password=default_database['PASSWORD'],
            dbname=default_database['NAME'],
            table=query,
            geometry_field='geometry',
        )

        layer = mapnik.Layer("Gemeenten", RD)
        layer.datasource = datasource

        layer.styles.append('RainappStyle')

        styles = {'RainappStyle': rainapp_style}
        layers = [layer]

        return layers, styles

    def legend(self, updates=None):
        slc = ShapeLegendClass.objects.get(descriptor=LEGEND_DESCRIPTOR)
        from lizard_shape.layers import AdapterShapefile
        la = {
            'layer_name': 'test',
            'resource_module': 'test',
            'resource_name': 'test',
            'legend_type': 'ShapeLegendClass',
            'legend_id': slc.id,
        }
        asf = AdapterShapefile(self.workspace_item, layer_arguments=la)
        return asf.legend(updates)

    def search(self, google_x, google_y, radius=None):
        """Search by coordinates, return matching items as list of dicts
        """

        rd_point_clicked = Point(*google_to_rd(google_x, google_y))
        geo_objects = GeoObject.objects.filter(
            geometry__contains=rd_point_clicked)

        result = []
        for g in geo_objects:
            maxdate = CompleteRainValue.objects.filter(
                parameterkey=self.parameterkey).aggregate(
                md=Max('datetime'))['md']
            if maxdate is not None:
                # If there is a maxdate, there must be a value at that date,
                # the import script should take care of that. However, it can be
                # a negative value, which is actually a statuscode.
                maxdate_site_tz = UTC.localize(maxdate).astimezone(self.tz)
                # import pdb;pdb.set_trace()
                value = g.rainvalue_set.get(datetime=maxdate,
                    parameterkey=self.parameterkey).value
                if value > -0.5:
                    popup_text = '%s: %.1f mm (%s)' % (
                        g.name,
                        value,
                        maxdate_site_tz.strftime('%d %b, %H:%M'))
                else:
                    popup_text = '%s: Geen data; code %i (%s)' % (
                        g.name,
                        value,
                        maxdate_site_tz.strftime('%d %b, %H:%M'))
            else:
                popup_text = '%s (Geen data)' % g.name
            identifier = {
                'location': g.municipality_id,
            }
            result.append({
                'identifier': identifier,
                'distance': 0,
                'workspace_item': self.workspace_item,
                # 'name': g.name + ' (' + str(maxdate) + ')',
                'name': popup_text,
                'shortname': g.name,
                'google_coords': (google_x, google_y),
            })

        return result

    def image(self,
              identifiers,
              start_date,
              end_date,
              width,
              height,
              layout_extra=None):
        """Return png image data for barchart."""
        today_site_tz = self.tz.localize(datetime.datetime.now())
        start_date_utc, end_date_utc = self._to_utc(start_date, end_date)
        graph = RainappGraph(start_date_utc,
                             end_date_utc,
                             width=width,
                             height=height,
                             today=today_site_tz,
                             tz=self.tz)

        # Gets timeseries, draws the bars, sets  the legend
        for identifier in identifiers:
            location_name = self._get_location_name(identifier)
            cached_value_result = self._cached_values(identifier,
                                                      start_date_utc,
                                                      end_date_utc)
            dates_site_tz = [row['datetime'].astimezone(self.tz)
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
                    offset_dates = [d + offset for d in dates_site_tz]
                else:
                    # We can only draw spikes.
                    bar_width = 0
                    offset_dates = dates_site_tz
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
        more'. Else the cache will always miss. Expects and returns UTC
        datetimes, with or without tzinfo
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

    def rain_stats(self,
                   values,
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
                't': self._t_to_string(None)}

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
                'datetime_start_utc'].astimezone(self.tz)
        else:
            datetime_start_site_tz = None
        if max_value['datetime_end_utc'] is not None:
            datetime_end_site_tz = max_value[
                'datetime_end_utc'].astimezone(self.tz)
        else:
            datetime_end_site_tz = None

        return {
            'td_window': td_window,
            'max': max_value['value'],
            'start': datetime_start_site_tz,
            'end': datetime_end_site_tz,
            't': self._t_to_string(t)}

    def html(self, snippet_group=None, identifiers=None, layout_options=None):
        """
        Popup with graph - table - bargraph.
        """
        logger.info('parameterkey: %s' % self.parameterkey)
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

        # Convert start and end dates to utc.
        start_date_utc, end_date_utc = self._to_utc(start_date, end_date)

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

            values = self._cached_values(identifier,
                                         start_date_utc,
                                         end_date_utc)

            area_m2 = GeoObject.objects.get(
                municipality_id=identifier['location']).geometry.area
            area_km2 = meter_square_to_km_square(area_m2)

            period_summary_row = {
                'td_window': 'periode',
                'max': sum([v['value'] for v in values]),
                'start': start_date,
                'end': end_date,
                't': self._t_to_string(None),
            }

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
                'period_summary_row': period_summary_row,
                'table': [self.rain_stats(values,
                                          area_km2,
                                          td_window,
                                          start_date_utc,
                                          end_date_utc)
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
