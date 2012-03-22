# -*- coding: utf-8 -*-
# Copyright 2011 Nelen & Schuurmans
import logging

from django.core.management.base import BaseCommand

from lizard_shape.models import ShapeTemplate
from lizard_shape.models import ShapeLegendClass
from lizard_shape.models import ShapeLegendSingleClass

logger = logging.getLogger(__name__)


def replace_legend():
    # Probably enough to just clear the rainapp template, since django's delete
    # Will be cascading.
    sts = ShapeTemplate.objects.filter(name='Rainapp')
    for st in sts:
        st.delete()

    st = ShapeTemplate(name='Rainapp',
                       id_field='Id field (unused)',
                       name_field='Name field (unused)',)

    st.save()

    slc = ShapeLegendClass(descriptor='Rainapp',
                           shape_template=st,
                           value_field='Value field (unused)',)

    slc.save()

    legend_props = [
        {'color': '8e36ed', 'index': 1, 'label': u'>=25',
         'max_value': u'', 'min_value': u'25'},
        {'color': 'ac25a5', 'index': 2, 'label': u'>=10',
         'max_value': u'25', 'min_value': u'10'},
        {'color': 'd21450', 'index': 3, 'label': u'>=5',
         'max_value': u'10', 'min_value': u'5'},
        {'color': 'fe0002', 'index': 4, 'label': u'>=2',
         'max_value': u'5', 'min_value': u'2'},
        {'color': '0001fe', 'index': 5, 'label': u'>=1',
         'max_value': u'2', 'min_value': u'1'},
        {'color': '374cff', 'index': 6, 'label': u'>=0,1',
         'max_value': u'1', 'min_value': u'0.1'},
        {'color': '7294ff', 'index': 7, 'label': u'>=0,05',
         'max_value': u'0.1', 'min_value':u'0.05'},
        {'color':'abdfff', 'index': 8, 'label':u'>=0,01',
         'max_value':u'0.05', 'min_value':u'0.01'},
        {'color':'ffffff', 'index':9, 'label':u'>=0',
         'max_value':u'0.01', 'min_value':u'0'},
        {'color':'000000', 'index':10, 'label':u'Geen data',
         'max_value':u'-0.5', 'min_value':u'-1.5'},
    ]

    slsc_kwargs = {'shape_legend_class': slc}
    for p in legend_props:
        p['color_inside'] = p['color']
        slsc_kwargs.update(p)
        ShapeLegendSingleClass(**slsc_kwargs).save()


class Command(BaseCommand):
    args = ""
    help = "TODO"

    def handle(self, *args, **options):
        replace_legend()
