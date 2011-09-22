Changelog of lizard-rainapp
===================================================


0.6 (unreleased)
----------------

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
