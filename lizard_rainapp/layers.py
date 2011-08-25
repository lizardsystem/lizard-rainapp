from django.template.loader import render_to_string

from lizard_fewsjdbc.layers import FewsJdbc


class RainAppAdapter(FewsJdbc):
    """
    Adapter for Rain app.
    """

    def html(self, snippet_group=None, identifiers=None, layout_options=None):

        symbol_url = self.symbol_url()
        img_url = ""

        return render_to_string(
            'lizard_rainapp/popup_rainapp.html',
            {'symbol_url': symbol_url,
             'img_url': img_url})
