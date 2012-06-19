Changelog of lizard-rainapp
===================================================


1.6 (unreleased)
----------------

- Nothing changed yet.


1.5 (2012-06-19)
----------------

- Some popup styling.

- Remove old graph.

- Fix cron job stopping on missing timeseries (24h measurements). Skip importing those instead.


1.4 (2012-06-01)
----------------

- Add support for FlotGraph.


1.3 (2012-05-29)
----------------

- Fixed UI.


1.2.8 (2012-05-18)
------------------

- Added MANIFEST.in.


1.2.7 (2012-05-18)
------------------

- Small development fix (.gitignore).


1.2.6 (2012-05-14)
------------------

- Add dependency on fewsjdbc to migrations


1.2.5 (2012-05-10)
------------------

- Nothing changed yet.


1.2.4 (2012-05-10)
------------------

- _Really_ fixes #3564 (the bug was a wrong indentation level of two
  lines -- curses, Python!)


1.2.3 (2012-05-04)
------------------

- Nothing changed yet.


1.2.2 (2012-05-04)
------------------

- Nothing changed yet.


1.2.1 (2012-05-04)
------------------

- Fixes issue #3564 (to do with the one below).


1.2 (2012-05-03)
----------------

- Only import data going 2 days back.

- In the 'rainapp_import_recent_data' management command, *always*
  import data, independent of the existence of a CompleteRainvalue
  value: because of the way 5 minute / hour / 24 hour values are
  interpolated in FEWS, they CAN CHANGE after initial import. In
  particular, some values always start out at 0 and are only correct
  to their true values several hours later.


1.1.3 (2012-03-23)
------------------

- Fixed bad UTF8 character in Waterschappen shapefile.


1.1.2 (2012-03-22)
------------------

- Removed 'CODE' field of a geoobject. It was unused, and giving
  problems at the same time.


1.1.1 (2012-03-22)
------------------

- Slugs in rainapp.cfg were wrong.


1.1 (2012-03-22)
----------------

- Added Waterschappen shapefiles, config. Using the default
  shapefiles now requires creating a RainappConfig instance in the
  admin interface.


1.0 (2012-03-22)
----------------

- Made import scripts, layers more generic so that multiple shapefiles
  can be used on the same site. This also means more configuration;
  see README.

- Added lizard-map as a dependency because rainapp depends on it.

- Added testdata and some tests.

0.9 (2012-02-09)
----------------

- Added "mm/h" besides "mm/hr".


0.8 (2012-01-12)
----------------

- Fixes bug where several locations in the same popup would have the
  same graph.


0.7 (2011-12-08)
----------------

- Fixed IE7 issue with too wide tables.

- Fixed add to collage button.

- Apparently fixed 24h issue without being aware of it
  (at least, it works now on my development system).


0.6 (2011-11-25)
----------------

- Re-enabled layer & legend, so that it can be used for individual
  municipalities (Almere, Heerhugowaard).

- Uses several optional settings in settings.py:
  RAINAPP_SHAPEFILE, RAINAPP_ID_FIELD, RAINAPP_NAME_FIELD,
  RAINAPP_CODE_FIELD, RAINAPP_X_FIELD, RAINAPP_Y_FIELD,
  RAINAPP_AREA_FIELD

  Without them, RainApp uses defaults that amount to loading the
  municipalities data.

- Settings RAINAPP_USE_SHAPES decides whether to draw the shapes
  or just user standard icons

0.5.8 (2011-11-23)
------------------

- Updates to Lizard 3.

- Changed 'Tijdspanne' to 'Periode' and 'Max (mm)' to 'mm'.

0.5.7 (2011-11-14)
------------------

- Added Setting model, admin and migration.


0.5.6 (2011-10-06)
------------------

- Temporarily disabled layer & legend until fast rainapp data retrieval becomes
  possible.


0.5.5 (2011-09-27)
------------------

- Adjusted statistics table so it reads T ≤ 1 if appropriate.


0.5.4 (2011-09-26)
------------------

- Removed warning level logging, putting negative precipitation values instead;
  to prevent overly cluttering of Sentry.

- Improved import recent data import script, so that it only queries fews when
  it is really needed.


0.5.3 (2011-09-22)
------------------

- Today line in graph now shows correct time in correct timezone.

- Fixed bug where no graph was shown when no coloring data is available.

- Added error checking in data import script.


0.5.2 (2011-09-20)
------------------

- Changed legend to include value and meaningful no data message if no data.

- Made layer display popup and graph and stats in site timezone instead of UTC.

- Fixed tests.

- Pinned latest nens-graph.


0.5.1 (2011-09-19)
------------------

- Removed the hardcoded fewsjdbc offset, since a new jdbc2ei corrected the
  problem.

- Changed a number o logger.debugs into logger.warns in the data import script.


0.5 (2011-09-15)
----------------

- Added model MunicipalityPolygon.

- Renamed adapters bar_image to image and removed all extra urls and views.

- Added shape and import script for municipality objects.

- Added script to import fewsdata for a single datetime of all municipalities.

- Added layer method to adapter that municipalities according to a lizard_shape
  legend

- Added search method to adapter that does a spatial query on the database

- Modified the statistics so that the 'herhalingstijd' is now based on the real
  area of the municipalities.

- Added test for the conversion of square meters to square km.

- changed database setting in testsettings to postgis database, otherwise tests
  don't work.

- Added script for creation of legend.

- Modified html_popup to be able to show T < 1.

- Modified fews import script to delete data older than 3 days, and to keep
  track of completely imported sets (for the whole country), and to add a -1
  value when there is no data.

- Modified the legend creation script to incorporate -1 (no data).

- Modified the layer so that it shows shapes if no recent values are available.

- Added a model that keeps track of the available complete local rainvalues.

- Added initial migration.

- Modified hover popup to incorporate datestamp of coloring


0.4 (2011-09-07)
----------------

- Made calculations better suited for 24 hour data at arbitrary hour of day.

- Moved max_values calculation to calculations.py and renamed to moving_sum.

- Added tests for max_values calculation.

- Moved all specific tests to test_calculations.py

- Improved moving_sum so that it skips possible values before start_date.

- Fixed #3194, Multiple graphs if multiple locations.

- Fixed bug in _cached_values if there are no values.


0.3 (2011-09-01)
----------------

- Using django json util now.


0.2 (2011-09-01)
----------------

- #3184 Removed graph from popup, put barchart on top.

- Changed location id's to location names

- Fixed collage screen error

- Added export button in popup and collagescreen

- Added (mm) to max in rainstats

- Fixed bug in max calculation that neglected first value

- Adjusted max calculation that now only uses data that fully fit in the
  window


0.1 (2011-08-30)
----------------

- Added 'home screen' template. It points to jdbc sources as rainapp urls.

- Created and switched to specialized graph in nens-graph library that has
  with better legend positioning.

- Working rain statistics table.

- Added method to draw bar graphs. Added RainGraph to place the legend
  below the graph. [Alex]

- Initial library skeleton created by nensskel.  [Jack]
