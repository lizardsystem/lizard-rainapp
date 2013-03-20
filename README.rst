lizard-rainapp
==========================================

Description
-----------

Rainapp shows a barchart and some statistics for precipitation data. It also
colors shapes that can be related to the fews locations (presently
municipalities)

Use ``bin/django import_geoobject_shapefile`` once to import the shapefiles. If used
again, the previous import is deleted.

Use ``bin/django rainapp_replace_legend`` to install or replace the required
legend in lizard_shape.

Use ``bin/django rainapp_import_recent_data`` to start extraction of the most recent
data from the fews datasource into a local table for coloring of the map.


Configuration
-------------

RainApp has been made a bit more generic and therefore needs more
configuration to work in your specific situation. There are three main
configuration things:

1. One or more shapefiles, all in the same directory, and one .cfg file to
   bind them. This file is in typical ConfigParser format with one section
   per shapefile. The names of the sections are not used anywhere. Use them
   to make the .cfg file readable. A section defines the RainappConfig slug
   that is related to this shapefile, and which fieldnames in the shapefile
   correspond to what. For instance, this is Almere's almere.cfg::

       [Afvoervlakken]
       shapefile=Afvoervlakken.shp
       id_field=GAFIDENT
       name_field=GAFNAAM
       code_field=GAFNAAM
       x_field=X
       y_field=Y
       area_field=SHAPE_AREA
       slug=afvoervlakken

       [AlmereGebieden]
       shapefile=AlmereGebieden.shp
       id_field=ID_NS
       name_field=ID
       x_field=X
       y_field=Y
       area_field=AREA
       slug=bemalingsgebieden

   Note that there is no path info, only a filename. The shapefiles must be
   in the same directory as the .cfg file.

2. Two settings.py options, ``RAINAPP_CONFIGFILE`` and
   ``RAINAPP_USE_SHAPES``.

   ``RAINAPP_CONFIGFILE`` is the mandatory full pathname to the above
   mentioned .cfg file. It is helpful to use pkg_resources, e.g.::

       RAINAPP_CONFIGFILE = resource_filename('almere',
                                              'shape/almere.cfg')

   Default: ``shape/rainapp.cfg`` in lizard_rainapp. To use this default, you
   must create a ``RainappConfig`` (slugs gemeentenconfig and
   waterschappenconfig) in the admin interface!

   ``RAINAPP_USE_SHAPES`` is a boolean. If True, use the shapes from the
   shapefile to draw the layer, otherwise fall back to a normal fewsjdbc layer
   (faster). Default to False.

3. RainappConfigs in the admin interface. These have four fields:

   **name**: used in a few messages and the admin interface (_not_ in the
   Lizard interface)

   **slug**: unique string to define this config. This is the slug that the
   .cfg file refers to.

   **jdbcsource** and **filter_id**: which jdbcsource and filter_id the data
   for this RainApp instance comes from.
