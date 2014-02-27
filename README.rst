lizard-rainapp
==========================================

Description
-----------

Rainapp shows a barchart and some statistics for precipitation data. It also
colors shapes that can be related to the fews locations (presently
municipalities)

Use ``bin/django rainapp_replace_legend`` to install or replace the required
legend in lizard_shape.

Use ``bin/django rainapp_import_recent_data`` to start extraction of the most recent
data from the fews datasource into a local table for coloring of the map.


Configuration
-------------

RainApp is a wrapper around FEWSJDBC that shows extra statistics along
with the popup graph, and can map (x, y) points in regions to FEWSJDBC
location IDs.

To create a working wrapper around some existing FEWSJDBC filter,
create a RainappConfig object in the admin interface.

Then visit the /rainapp/beheer/ URL to upload a shapefile for the mapping.
