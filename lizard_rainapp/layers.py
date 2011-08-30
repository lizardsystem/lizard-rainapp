import datetime
import json
import logging
import iso8601

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.http import Http404
from django.http import HttpResponse

from lizard_fewsjdbc.layers import FewsJdbc
from lizard_map.adapter import Graph
from lizard_map.daterange import current_start_end_dates
from lizard_rainapp.calculations import herhalingstijd

from nens_graph.rainapp import RainappGraph

logger = logging.getLogger(__name__)


class RainGraph(Graph):
    """
    Class inheres from Graph class of lizard_map.adapter
    - overrides the legend method
    """

    def legend_font_size(self, max_label_len):
        """
        Defines the font size depended on graph width and max label length
        """
        if max_label_len > 65 * ((self.width - 150) / 314.0):
            return 'xx-small'
        if max_label_len > 50 * ((self.width - 150) / 314.0):
            return 'x-small'
        if max_label_len > 40 * ((self.width - 150) / 314.0):
            return 'small'
        return 'medium'

    def legend(self,
               handles=None,
               labels=None,
               ncol=1,
               force_legend_below=False):
        """
        Displays legend under the graph.

        Handles is list of matplotlib objects (e.g. matplotlib.lines.Line2D)
        labels is list of strings
        """
        if handles is None and labels is None:
            handles, labels = self.axes.get_legend_handles_labels()

        if handles and labels:
            max_label_len = max([len(label) for label in labels])
            font_size = self.legend_font_size(max_label_len)
            prop = {'size': font_size}

            return self.axes.legend(
                handles,
                labels,
                bbox_to_anchor=(0., -0.15, 1, .102),
                prop=prop,
                loc="upper left",
                ncol=ncol,
                mode="expand",
                fancybox=True,
                shadow=True,)


class RainAppAdapter(FewsJdbc):
    """
    Adapter for Rain app.

    identifier: {'location': <locationid>}
    """

    def get_bar_width(self, values, unit, graph):
        """
        Calculates the width of the bar.
        """
        if unit == 'mm/24hr':
            return graph.width / len(values) / 500
        elif unit == 'mm/3hr':
            return graph.width / len(values) / 700
        elif unit == 'mm/hr':
            return graph.width / len(values) / 800
        elif unit == 'mm/5min':
            return graph.width / len(values) / 1000
        else:
            return 0.8

    def bar_image(self, identifiers, start_date, end_date, width, height):
        """Implement bar_image.

        gebruik self.values(identifier, start_date, end_date) en/of
        self.value_aggregate_default(...) -> see lizard_map.workspace

        """
        today = datetime.datetime.now()
        named_locations = self._locations()
        graph = RainGraph(start_date, end_date,
                      width=width, height=height, today=today)
        # Uses first identifier and breaks the loop
        # Gets timeseries, draws the bars, sets  the legend
        for identifier in identifiers:
            location_id = identifier['location']
            location_name = [
                location['location'] for location in named_locations
                if location['locationid'] == location_id][0]
            timeseries = self._cached_values(identifier, start_date, end_date)
            dates = [row['datetime'] for row in timeseries]
            values = [row['value'] for row in timeseries]
            units = [row['unit'] for row in timeseries]
            unit = ''
            if len(units) > 0:
                unit = units[0]
            if values:
                graph.axes.bar(dates, values, lw=1,
                               edgecolor='blue',
                               width=self.get_bar_width(values, unit, graph),
                               label=location_name)
            graph.axes.set_ylabel(unit)
            graph.legend()
            break  # Only render the first item

        return graph.http_png()

    def image(self,
              identifiers,
              start_date,
              end_date,
              width=380.0,
              height=250.0,
              layout_extra=None,
              raise_404_if_empty=False):

        """
        Visualize timeseries in a graph.

        Legend is always drawn.

        TODO: option x-label does not work. Graph is too high?
        TODO: y_min, y_max does not work.
        """

        def apply_layout(layout, title, y_min, y_max, legend):
            """Applies layout options. Returns title,
            y_min, y_max, graph, legend

            From lizard-fewsunblobbed"""

            if "title" in layout:
                title = layout['title']
            if "y_min" in layout:
                y_min = float(layout['y_min'])
            if "y_max" in layout:
                y_max = float(layout['y_max'])
            if "legend" in layout:
                legend = layout['legend']
            if "y_label" in layout:
                graph.set_ylabel(layout['y_label'])
            if "x_label" in layout:
                graph.set_xlabel(layout['x_label'])
            return title, y_min, y_max, legend

        def apply_lines(identifier, values, location_name):
            """Adds lines that are defined in layout. Uses function
            variable graph, line_styles.

            Inspired by fewsunblobbed"""

            layout = identifier['layout']

            if "line_min" in layout:
                graph.axes.axhline(
                    min(values),
                    color=line_styles[str(identifier)]['color'],
                    lw=line_styles[str(identifier)]['min_linewidth'],
                    ls=line_styles[str(identifier)]['min_linestyle'],
                    label='Minimum %s' % location_name)
            if "line_max" in layout:
                graph.axes.axhline(
                    max(values),
                    color=line_styles[str(identifier)]['color'],
                    lw=line_styles[str(identifier)]['max_linewidth'],
                    ls=line_styles[str(identifier)]['max_linestyle'],
                    label='Maximum %s' % location_name)
            if "line_avg" in layout and values:
                average = sum(values) / len(values)
                graph.axes.axhline(
                    average,
                    color=line_styles[str(identifier)]['color'],
                    lw=line_styles[str(identifier)]['avg_linewidth'],
                    ls=line_styles[str(identifier)]['avg_linestyle'],
                    label='Gemiddelde %s' % location_name)

        line_styles = self.line_styles(identifiers)
        named_locations = self._locations()
        today = datetime.datetime.now()
        # graph = Graph(start_date, end_date,
        #               width=width, height=height, today=today)
        graph = RainappGraph(start_date, end_date,
                      width=width, height=height, today=today)
        graph.axes.grid(True)

        # Draw extra's (from fewsunblobbed)
        title = None
        y_min, y_max = None, None
        legend = None

        is_empty = True
        unit = None
        for identifier in identifiers:
#           filter_id = self.filterkey
#           location_id = identifier['location']
#           location_name = [
#               location['location'] for location in named_locations
#               if location['locationid'] == location_id][0]

#           parameter_id = self.parameterkey
#           timeseries = self.jdbc_source.get_timeseries(
#               filter_id, location_id, parameter_id, start_date, end_date)
#           if timeseries:
#               is_empty = False
#           # Plot data if available.
            cached_value_result = self._cached_values(identifier,
                                                      start_date,
                                                      end_date)
#           dates = [row['time'] for row in timeseries]
#           values = [row['value'] for row in timeseries]
            dates = [row['datetime'] for row in cached_value_result]
            values = [row['value'] for row in cached_value_result]

            location_id = identifier['location']
            location_name = [
                location['location'] for location in named_locations
                if location['locationid'] == location_id][0]
            if not unit:
                unit = cached_value_result[0]['unit']

            if values:
                is_empty = False
                graph.axes.plot(dates, values,
                                lw=1,
                                color=line_styles[str(identifier)]['color'],
                                label=location_name)
            # Apply custom layout parameters.
            if 'layout' in identifier:
                layout = identifier['layout']
                title, y_min, y_max, legend = apply_layout(
                    layout, title, y_min, y_max, legend)
                apply_lines(identifier, values, location_name)

        if is_empty and raise_404_if_empty:
            raise Http404

        if identifiers:
            layout = identifiers[0].get('layout')
            if layout:
                if layout.get('legend'):
                    # Ok, this 'if' tree is a bit rediculously deep.
                    #graph.legend(force_legend_below=True)
                    graph.legend()
                    # If there is not data, graph.axes.legend_ is None
                    if graph.axes.legend_ is not None:
                        graph.axes.legend_.draw_frame(False)

        # Extra layout parameters. From lizard-fewsunblobbed.
        if y_min is None:
            y_min, _ = graph.axes.get_ylim()
        if y_max is None:
            _, y_max = graph.axes.get_ylim()

        if layout_extra:
            title, y_min, y_max, legend = apply_layout(
                layout_extra, title, y_min, y_max, legend)

        if title:
            graph.suptitle(title)
        if unit:
            graph.set_ylabel(unit)

        # TODO: set_ylim does not work.
        graph.axes.set_ylim(y_min, y_max)

        # Copied from lizard-fewsunblobbed.
        if "horizontal_lines" in layout_extra:
            for horizontal_line in layout_extra['horizontal_lines']:
                graph.axes.axhline(
                    horizontal_line['value'],
                    ls=horizontal_line['style']['linestyle'],
                    color=horizontal_line['style']['color'],
                    lw=horizontal_line['style']['linewidth'],
                    label=horizontal_line['name'])

        graph.add_today()

        graph.responseobject = HttpResponse(content_type='image/png')
        return graph.png_response()

    def _tzaware(self, dt, tzinfo):
        """Make datetime timezone aware"""
        return datetime.datetime(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second,
            tzinfo=tzinfo)

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
                end_date.year, end_date.month, end_date.day
                ) + datetime.timedelta(days=1))

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

        # Convert datetime strings to datetime in values
        for value in values:
            value['datetime'] = iso8601.parse_date(value['datetime_str'])
            del value['datetime_str']

        start_date = self._tzaware(start_date, values[0]['datetime'].tzinfo)
        end_date = self._tzaware(end_date, values[0]['datetime'].tzinfo)
        # Remove datetimes out of range.
        while values and values[0]['datetime'] < start_date:
            del values[0]
        while values and values[-1]['datetime'] > end_date:
            del values[-1]

        return values

    def rain_stats(self, values, td, start_date, end_date):
        """
        Calculate stats.

        TODO: make faster by caching the data.

        TODO: add herhalingstijd. needs: bui_duur [uren], oppervlakte
        [vierkante km] neerslag_som [mm]
        """
        logger.debug('Calculating rain stats for start=%s, end=%s, td=%s' %
                     (start_date, end_date, td))
        if not values:
            return {
                'td': td,
                'max': '-',
                'datetime': '-',
                'start': '-',
                'end': '-',
                't': '-'}

        # Make start_date and end_date tz aware
        start_date = self._tzaware(
            start_date,
            tzinfo=values[0]['datetime'].tzinfo)
        end_date = self._tzaware(
            end_date,
            tzinfo=values[0]['datetime'].tzinfo)

        max_values = []

        # Loop values and calc max for each period. Slow, but it works.

        # End_date often ends with 23:59:59, we want to include at
        # least 1 day in case td=1 day, thus the 2 seconds.
        end = end_date - td + datetime.timedelta(seconds=2)
        period_counter = start_date
        one_hour = datetime.timedelta(seconds=3600)

        # Fast way to calculate sum values.
        calc_first = False
        len_values = len(values)
        min_index, max_index = 0, 0
        sum_values = 0
        while period_counter < end:
            period_start = period_counter
            period_end = period_counter + td

            # Calculate value by subtracting value(s) from front and
            # adding new value(s) from end.
            while (max_index + 1 < len_values and
                   values[max_index+1]['datetime'] < period_end):

                sum_values += values[max_index + 1]['value']
                max_index += 1

            while (min_index < max_index and
                   values[min_index]['datetime'] < period_start):

                sum_values -= values[min_index]['value']
                min_index += 1

            max_values.append({
                    'value': sum_values, 'datetime': period_counter})

            period_counter += one_hour

        if max_values:
            max_value = max(max_values, key=lambda i: i['value'])
            max_value['datetime_end'] = max_value['datetime'] + td
            hours = td.days * 24 + td.seconds / 3600.0
            t = herhalingstijd(hours, 25, max_value['value'])
        else:
            max_value = {'value': '-', 'datetime': '-', 'datetime_end': '-'}
            t = '-'

        return {
            'td': td,
            'max': max_value['value'],
            'start': max_value['datetime'],
            'end': max_value['datetime_end'],
            't': t}

    def html(self, snippet_group=None, identifiers=None, layout_options=None):
        """
        Popup with graph - table - bargraph.
        """
        if snippet_group:
            identifiers = [
                snippet.identifier
                for snippet in snippet_group.snippets.filter(visible=True)]
        title = 'RainApp (%s)' % ', '.join(
            [identifier['location'] for identifier in identifiers])

        # Make table with these identifiers.
        # Layer options contain request - not the best way but it works.
        start_date, end_date = current_start_end_dates(
            layout_options['request'])

        # Contains list of tables. A table is a list of rows/dicts
        # with 'max', 'start', 'end', '..'
        rain_stats = {}

        td_range = [
            datetime.timedelta(days=2),
            datetime.timedelta(days=1),
            datetime.timedelta(hours=3),
            datetime.timedelta(hours=1)
            ]
        for identifier in identifiers:
            values = self._cached_values(identifier, start_date, end_date)
            rain_stats[identifier['location']] = []
            for td in td_range:
                rain_stats[identifier['location']].append(self.rain_stats(
                        values, td,
                        start_date, end_date))

        # Collect urls for graphs.
        symbol_url = self.symbol_url()
        if snippet_group:
            # Image url for snippet_group: can change if snippet_group
            # properties are altered.
            img_url = reverse(
                "lizard_map.snippet_group_image",
                kwargs={'snippet_group_id': snippet_group.id},
                )
            bar_url = reverse(
                "lizard_rainapp.snippet_group_rainapp_bars",
                kwargs={'snippet_group_id': snippet_group.id},
                )
        else:
            # Image url: static url composed with all options and
            # layout tweak.
            img_url = reverse(
                "lizard_map.workspace_item_image",
                kwargs={'workspace_item_id': self.workspace_item.id},
                )
            bar_url = reverse(
                "lizard_rainapp.workspace_item_rainapp_bars",
                kwargs={'workspace_item_id': self.workspace_item.id},
                )
            identifiers_escaped = [json.dumps(identifier).replace('"', '%22')
                                   for identifier in identifiers]
            url_extra = '?' + '&'.join(['identifier=%s' % i for i in
                                        identifiers_escaped])
            img_url += url_extra
            bar_url += url_extra

        return render_to_string(
            'lizard_rainapp/popup_rainapp.html',
            {'title': title,
             'rain_stats': rain_stats,
             'number_of_locations': len(rain_stats.keys()),
             'symbol_url': symbol_url,
             'img_url': img_url,
             'bar_url': bar_url})
