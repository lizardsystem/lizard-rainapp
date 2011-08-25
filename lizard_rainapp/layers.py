import datetime
import json

from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from lizard_fewsjdbc.layers import FewsJdbc
from lizard_map.adapter import Graph
from lizard_map.daterange import current_start_end_dates


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
        graph = Graph(start_date, end_date,
                      width=width, height=height, today=today)
        graph.add_today()

        return graph.http_png()


    def rain_stats(self, identifier, td, start_date, end_date):
        """
        Calculate stats
        """
        return {
            'td': td,
            'max': 'max',
            'start': 'start',
            'end': 'end',
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

        for identifier in identifiers:
            rain_stats.append(self.rain_stats(
                    identifier, datetime.timedelta(days=2),
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
