Changelog of lizard-rainapp
===================================================


0.5 (unreleased)
----------------

- Added model MunicipalityPolygon.

- Renamed adapters bar_image to image and removed all extra urls and views.

- Added shape and import script for municipality objects.


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
