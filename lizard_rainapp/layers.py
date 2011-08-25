import datetime
import json
import logging

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.http import Http404

from lizard_fewsjdbc.layers import FewsJdbc
from lizard_map.adapter import Graph
from lizard_map.daterange import current_start_end_dates

logger = logging.getLogger(__name__)


class RainAppAdapter(FewsJdbc):
    """
    Adapter for Rain app.

    identifier: {'location': <locationid>}
    """

    def bar_image(self, identifiers, start_date, end_date, width, height):
        """Implement bar_image.

        gebruik self.values(identifier, start_date, end_date) en/of
        self.value_aggregate_default(...) -> see lizard_map.workspace

        """
        today = datetime.datetime.now()
        named_locations = self._locations()
        line_styles = self.line_styles(identifiers)
        graph = RainGraph(start_date, end_date,
                      width=width, height=height, today=today)

        is_empty = True
        # Uses first identifier and breaks the loop
        # Gets timeseries, draws the bars, sets  the legend
        for identifier in identifiers:
            location_id = identifier['location']
            location_name = [
                location['location'] for location in named_locations
                if location['locationid'] == location_id][0]
            timeseries = self.values(identifier, start_date, end_date)
            if timeseries:
                is_empty = False
            dates = [row['datetime'] for row in timeseries]
            values = [row['value'] for row in timeseries]
            units = [row['unit'] for row in timeseries]
            if len(units) > 0:
                graph.axes.set_ylabel(units[0])
            if values:
                graph.axes.bar(dates, values, lw=1,
                                color=line_styles[str(identifier)]['color'],
                                label=location_name)
            graph.legend()
            break

        if is_empty:
            raise Http404

        return graph.http_png()

    # def _cached_values(self, identifier, start_date, end_date):
    #     """
    #     Same as self.values, but cached.

    #     The stored values are rounded in days, a 'little bit
    #     more'. Else the cache will always miss.
    #     """
    #     start_date_cache = datetime.datetime(
    #         start_date.year, start_date.month, start_date.day)
    #     end_date_cache = (
    #         datetime.datetime(
    #             end_date.year, end_date.month, end_date.day
    #             ) + datetime.timedelta(days=1))
    #     cache_key = hash('%s::%s::%s::%s::%s::%s' % (
    #             self.jdbc_source.id, self.filterkey, self.parameterkey,
    #             identifier['location'], start_date_cache, end_date_cache))
    #     values = cache.get(cache_key)
    #     if values is None:
    #         logger.debug('Caching values for %s' % identifier['location'])
    #         values = self.values(identifier, start_date, end_date)
    #         cache.set(cache_key, values)

    #     print start_date
    #     print values[0]['datetime']
    #     # Remove datetimes out of range.
    #     # Problem: tz aware and tz naive datetimes cannot be compared
    #     while values and values[0]['datetime'] < start_date:
    #         del values[0]
    #     while values and values[-1]['datetime'] > end_date:
    #         del values[-1]

    #     return values

    def rain_stats(self, identifier, td, start_date, end_date):
        """
        Calculate stats.

        TODO: make faster by caching the data.
        """
        check_start = start_date - td
        check_end = start_date
        values = self.values(identifier, check_start, check_end)
        if values:
            max_value = max(values, key=lambda i: i['value'])
        else:
            max_value = {'value': 'geen waardes', 'datetime': '-'}
        return {
            'td': td,
            'max': max_value['value'],
            'datetime': max_value['datetime'],
            'start': check_start,
            'end': check_end,
            't': 'herhalingstijd'}

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
        rain_stats = []  # Contains dicts with 'max', 'start', 'end', '..'

        td_range = [
            datetime.timedelta(days=2),
            datetime.timedelta(days=1),
            datetime.timedelta(hours=3),
            datetime.timedelta(hours=1)
            ]
        for identifier in identifiers:
            for td in td_range:
                rain_stats.append(self.rain_stats(
                        identifier, td,
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
             'symbol_url': symbol_url,
             'img_url': img_url,
             'bar_url': bar_url})


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
