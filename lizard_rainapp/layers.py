# -*- coding: utf-8 -*-
from __future__ import division
import datetime
import iso8601
import locale
import logging
import mapnik
import pytz

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.db.models import Max
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import simplejson as json
from lizard_fewsjdbc.layers import FewsJdbc
from lizard_map.adapter import FlotGraph
from lizard_map.coordinates import RD
from lizard_map.coordinates import google_to_rd
from lizard_map.daterange import current_start_end_dates
from lizard_shape.models import ShapeLegendClass
from nens_graph.rainapp import RainappGraph

from lizard_rainapp.calculations import UNIT_TO_TIMEDELTA
from lizard_rainapp.calculations import meter_square_to_km_square
from lizard_rainapp.calculations import rain_stats
from lizard_rainapp.calculations import t_to_string
from lizard_rainapp.models import CompleteRainValue
from lizard_rainapp.models import GeoObject
from lizard_rainapp.models import RainappConfig

logger = logging.getLogger(__name__)

# Requires correct locale be generated on the server.
# On ubuntu: check with locale -a
# On ubuntu: sudo locale-gen nl_NL.utf8
try:
    locale.setlocale(locale.LC_TIME, 'nl_NL.UTF8')
except locale.Error:
    logger.debug('No locale nl_NL.UTF8 on this os. Using default locale.')

LEGEND_DESCRIPTOR = 'Rainapp'
UTC = pytz.timezone('UTC')


class RainAppAdapter(FewsJdbc):
    """
    Adapter for Rain app.

    identifier: {'location': <locationid>}
    """
    support_flot_graph = True

    def __init__(self, *args, **kwargs):
        super(RainAppAdapter, self).__init__(
            *args, **kwargs)

        self.tz = pytz.timezone(settings.TIME_ZONE)

        try:
            self.rainapp_config = RainappConfig.objects.get(
                jdbcsource=self.jdbc_source, filter_id=self.filterkey)
        except RainappConfig.DoesNotExist:
            self.rainapp_config = None

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

    def _get_location_name(self, identifier):
        """Return location_name for identifier."""
        named_locations = self._locations()
        location_id = identifier['location']

        location_names = [
            location['location'] for location in named_locations
            if location['locationid'] == location_id]

        if location_names:
            return location_names[0]
        else:
            logger.warn("_get_location_name: Location names is empty;" +
                        " looking for location_id=%s in named_locations %s." %
                        (location_id, named_locations))
            return "Unknown location"  # TODO

    def layer(self, *args, **kwargs):
        """Return mapnik layers and styles."""

        if not self.rainapp_config:
            # Fall back to FEWSJDBC.
            return super(RainAppAdapter, self).layer(*args, **kwargs)

        slc = ShapeLegendClass.objects.get(descriptor=LEGEND_DESCRIPTOR)
        rainapp_style = slc.mapnik_style()

        self.maxdate = (CompleteRainValue.objects.filter(
                parameterkey=self.parameterkey, config=self.rainapp_config)
                        .aggregate(md=Max('datetime'))['md'])

        if self.maxdate is None:
            # Color all shapes according to value -1
            query = """(
                select
                    -1 as value,
                    gob.geometry as geometry
                from
                    lizard_rainapp_geoobject gob
                where
                    gob.config_id = '%d'
            ) as data""" % (self.rainapp_config.pk,)
        else:
            # For the query to behave properly, time zone information must be
            # passed! For naive datetime, %Z will be formatted as an empty
            # string, so that case is covered as well.
            maxdate_str = self.maxdate.strftime('%Y-%m-%dT%H:%M:%S%Z')

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
                    rav.parameterkey = '%s' and
                    gob.config_id = '%d'
            ) as data""" % (maxdate_str, self.parameterkey,
                            self.rainapp_config.pk)

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
        "Search by coordinates, return matching items as list of dicts"

        logger.debug("google_x " + str(google_x))
        logger.debug("google_y " + str(google_y))

        rd_point_clicked = Point(*google_to_rd(google_x, google_y))
        if not self.rainapp_config:
            return None

        geo_objects = GeoObject.objects.filter(
            geometry__contains=rd_point_clicked,
            config=self.rainapp_config)

        result = []
        for g in geo_objects:
            maxdate = CompleteRainValue.objects.filter(
                parameterkey=self.parameterkey,
                config=self.rainapp_config).aggregate(
                md=Max('datetime'))['md']

            logger.debug('SEARCH maxdate = ' + str(maxdate))

            identifier = {
                'location': g.municipality_id,
            }
            result.append({
                'identifier': identifier,
                'distance': 0,
                'workspace_item': self.workspace_item,
                'name': '{}, {}'.format(g.name, self.parameter_name),
                'shortname': g.name,
                'google_coords': (google_x, google_y),
            })

        return result

    def image(
        self,
        identifiers,
        start_date,
        end_date,
        width,
        height,
        layout_extra=None
    ):
        """Return png image data for barchart."""
        return self._render_graph(
            identifiers,
            start_date,
            end_date,
            width=width,
            height=height,
            layout_extra=layout_extra,
            GraphClass=RainappGraph
        )

    def _render_graph(
        self,
        identifiers,
        start_date,
        end_date,
        layout_extra=None,
        raise_404_if_empty=False,
        GraphClass=RainappGraph,
        **extra_params
    ):
        today_site_tz = self.tz.localize(datetime.datetime.now())
        start_date_utc, end_date_utc = self._to_utc(start_date, end_date)
        graph = GraphClass(start_date_utc,
                             end_date_utc,
                             today=today_site_tz,
                             tz=self.tz,
                             **extra_params)

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

        return graph.render()

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

    def html(self, identifiers=None, layout_options=None):
        """
        Popup with graph - table - bargraph.
        """
        add_snippet = layout_options.get('add_snippet', False)

        parameter_name = self.parameter_name

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

        for identifier in identifiers:
            image_graph_url = self.workspace_mixin_item.url(
                "lizard_map_adapter_image", (identifier,))
            flot_graph_data_url = self.workspace_mixin_item.url(
                "lizard_map_adapter_flot_graph_data", (identifier,))

            values = self._cached_values(identifier,
                                         start_date_utc,
                                         end_date_utc)

            area_m2 = GeoObject.objects.get(
                municipality_id=identifier['location'],
                config=self.rainapp_config).geometry.area
            area_km2 = meter_square_to_km_square(area_m2)

            period_summary_row = {
                'max': sum([v['value'] for v in values]),
                'start': start_date,
                'end': end_date,
                'delta': (end_date - start_date).days,
                't': t_to_string(None),
            }
            infoname = '%s, %s' % (
                self._get_location_name(identifier), parameter_name)
            info.append({
                'identifier': identifier,
                'identifier_json': json.dumps(identifier).replace('"', '%22'),
                'shortname': infoname,
                'name': infoname,
                'location': self._get_location_name(identifier),
                'period_summary_row': period_summary_row,
                'table': [rain_stats(values,
                                     area_km2,
                                     td_window,
                                     start_date_utc,
                                     end_date_utc)
                          for td_window in td_windows],
                'image_graph_url': image_graph_url,
                'flot_graph_data_url': flot_graph_data_url,
                'url': self.workspace_mixin_item.url(
                        "lizard_map_adapter_values", [identifier, ],
                        extra_kwargs={'output_type': 'csv'}),
                'workspace_item': self.workspace_mixin_item,
                'adapter': self
            })

        return render_to_string(
            'lizard_rainapp/popup_rainapp.html',
            {
                'title': parameter_name,
                'symbol_url': symbol_url,
                'add_snippet': add_snippet,
                'workspace_item': self.workspace_item,
                'info': info
            }
        )

    ##
    # New for flot graphs
    ##

    def flot_graph_data(
        self,
        identifiers,
        start_date,
        end_date,
        layout_extra=None,
    ):
        return self._render_graph(
            identifiers,
            start_date,
            end_date,
            layout_extra=layout_extra,
            GraphClass=FlotGraph
        )
