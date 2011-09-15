lizard-rainapp
==========================================

Rainapp shows a barchart and some statistics for precipitation data. It also
colors shapes that can be related to the fews locations (presently
municipalities)

Use ``bin/django import_geoobject_shapefile`` once to import the shapefile. If used
again, the previous import is deleted.

Use ``bin/django rainapp_replace_legend`` to install or replace the required
legend in lizard_shape.

Use ``bin/django rainapp_import_recent_data`` to start extraction of the most recent
data from the fews datasource into a local table for coloring of the map.
