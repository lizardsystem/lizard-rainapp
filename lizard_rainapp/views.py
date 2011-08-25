# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
import datetime
import json

from django.shortcuts import get_object_or_404

from lizard_map.daterange import current_start_end_dates
from lizard_map.models import WorkspaceCollageSnippetGroup
from lizard_map.models import WorkspaceItem


def size_from_request(request):
    width = request.GET.get('width')
    height = request.GET.get('height')
    if width:
        width = int(width)
    else:
        # We want None, not u''.
        width = None
    if height:
        height = int(height)
    else:
        # We want None, not u''.
        height = None
    return width, height


def snippet_group_rainapp_bars(request, snippet_group_id):
    """
    Draw the bars view for given snippet group id.
    """
    snippet_group = WorkspaceCollageSnippetGroup.objects.get(
        pk=snippet_group_id)
    snippets = snippet_group.snippets.filter(visible=True)
    identifiers = [snippet.identifier for snippet in snippets]

    using_workspace_item = snippets[0].workspace_item
    start_date, end_date = current_start_end_dates(request)
    width, height = size_from_request(request)

    return using_workspace_item.adapter.bar_image(
        identifiers, start_date, end_date, width, height)


def workspace_item_rainapp_bars(request, workspace_item_id):
    """
    Draw the bars view for given workspace_item_id
    """
    identifier_json_list = request.GET.getlist('identifier')
    identifier_list = [json.loads(identifier_json) for identifier_json in
                       identifier_json_list]

    workspace_item = get_object_or_404(WorkspaceItem, pk=workspace_item_id)
    start_date, end_date = current_start_end_dates(request)
    width, height = size_from_request(request)

    return workspace_item.adapter.bar_image(
        identifier_list, start_date, end_date,
        width, height)
